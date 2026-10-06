"""
UM_TERRA_SENTINEL Agent — Core tools for live Earth intelligence.
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.

Provides tool functions consumed by the LangGraph agent:
  - fetch_earthquakes
  - fetch_natural_events
  - fetch_weather_cities
  - fetch_space_weather
  - fetch_iss_position
  - fetch_near_earth_objects
  - get_threat_index
  - get_active_alarms
  - get_sentinel_summary
"""
import json
import math
import time
import httpx
from datetime import datetime, timezone
from typing import Optional

from langchain_core.tools import tool

# ── Sentinel cities monitored by UM_Terra Sentinel ───────────────────────────
SENTINEL_CITIES = [
    {"n": "Kolkata",     "lat": 22.57,  "lon":  88.36},
    {"n": "Mumbai",      "lat": 19.08,  "lon":  72.88},
    {"n": "Tokyo",       "lat": 35.68,  "lon": 139.69},
    {"n": "Manila",      "lat": 14.60,  "lon": 120.98},
    {"n": "Sydney",      "lat": -33.87, "lon": 151.21},
    {"n": "London",      "lat": 51.51,  "lon":  -0.13},
    {"n": "New York",    "lat": 40.71,  "lon": -74.01},
    {"n": "Los Angeles", "lat": 34.05,  "lon": -118.24},
    {"n": "São Paulo",   "lat": -23.55, "lon": -46.63},
    {"n": "Cairo",       "lat": 30.04,  "lon":  31.24},
    {"n": "Lagos",       "lat":  6.52,  "lon":   3.38},
    {"n": "Dubai",       "lat": 25.20,  "lon":  55.27},
]

# ── Allowed outbound hosts (mirrors browser CSP) ─────────────────────────────
_ALLOWED_HOSTS = {
    "earthquake.usgs.gov",
    "eonet.gsfc.nasa.gov",
    "api.open-meteo.com",
    "air-quality-api.open-meteo.com",
    "services.swpc.noaa.gov",
    "api.wheretheiss.at",
    "api.nasa.gov",
}

_TIMEOUT = 14.0   # seconds
_MAX_BYTES = 6_000_000


def _safe_fetch(url: str) -> dict:
    """
    Validated HTTPS-only fetch restricted to the allow-list.
    Returns parsed JSON or raises on any error.
    """
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError(f"Non-HTTPS URL blocked: {url}")
    host = parsed.netloc.split(":")[0].lower()
    if host not in _ALLOWED_HOSTS:
        raise ValueError(f"Host not in allow-list: {host}")
    with httpx.Client(timeout=_TIMEOUT, follow_redirects=False) as client:
        r = client.get(url, headers={"User-Agent": "UM-TERRA-SENTINEL-Agent/1.0"})
        r.raise_for_status()
        if len(r.content) > _MAX_BYTES:
            raise ValueError("Response too large")
        return r.json()


def _quake_severity(mag: float, tsunami: bool = False) -> int:
    s = 0 if mag < 4 else 1 if mag < 5 else 2 if mag < 6 else 3 if mag < 7 else 4
    if tsunami and s < 4 and mag >= 6:
        s += 1
    return s


def _eonet_severity(cat: str, mag, unit: str) -> int:
    u = (unit or "").lower()
    if cat == "wildfire":
        if mag is None:
            return 1
        ac = mag * 2.47 if "ha" in u else mag
        return 3 if ac >= 50000 else 2 if ac >= 5000 else 1
    if cat == "storm":
        if mag is None:
            return 2
        kt = mag if ("kts" in u or "kt" in u) else mag / 1.852
        return 4 if kt >= 113 else 3 if kt >= 64 else 2 if kt >= 34 else 1
    if cat == "volcano":
        return 2
    if cat == "flood":
        return 2
    if cat == "drought":
        return 1
    if cat == "ice":
        return 0
    return 1


_EONET_MAP = {
    "wildfires": "wildfire", "severeStorms": "storm", "volcanoes": "volcano",
    "floods": "flood", "drought": "drought", "seaLakeIce": "ice",
    "snow": "ice", "earthquakes": "earthquake",
}

_SEV_NAME = ["MINOR", "ADVISORY", "WATCH", "WARNING", "CRITICAL"]
_CATS = {
    "earthquake": "Earthquakes", "storm": "Storms", "wildfire": "Wildfires",
    "volcano": "Volcanoes",      "flood": "Floods",  "drought": "Drought",
    "ice": "Ice",                "other": "Other events",
}


# ─────────────────────────────────────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────────────────────────────────────

@tool
def fetch_earthquakes(min_magnitude: float = 2.5, max_results: int = 20) -> str:
    """
    Fetch recent earthquakes from USGS.
    Returns a JSON list of earthquake events sorted by severity/magnitude.
    Each entry contains: id, title, latitude, longitude, magnitude, depth_km,
    severity (0-4), time_utc, source, tsunami_flag, confidence.
    Falls back to simulated data if the feed is unreachable.

    Args:
        min_magnitude: Minimum magnitude to include (default 2.5).
        max_results: Maximum number of results to return (default 20).
    """
    try:
        data = _safe_fetch(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        )
        features = data.get("features", [])
        events = []
        for f in features:
            p = f.get("properties", {})
            g = (f.get("geometry") or {}).get("coordinates", [])
            if len(g) < 2:
                continue
            mag = p.get("mag")
            if mag is None or float(mag) < min_magnitude:
                continue
            mag = float(mag)
            events.append({
                "id": f.get("id", ""),
                "title": p.get("place", "Unknown region"),
                "latitude": round(float(g[1]), 4),
                "longitude": round(float(g[0]), 4),
                "magnitude": round(mag, 1),
                "depth_km": round(float(g[2]), 1) if len(g) > 2 else None,
                "severity": _quake_severity(mag, p.get("tsunami") == 1),
                "severity_label": _SEV_NAME[_quake_severity(mag, p.get("tsunami") == 1)],
                "time_utc": datetime.fromtimestamp(
                    p["time"] / 1000, tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ") if p.get("time") else None,
                "source": "USGS (live)",
                "tsunami_flag": p.get("tsunami") == 1,
                "confidence": "Reviewed (high)" if p.get("status") == "reviewed" else "Automatic (moderate)",
                "simulated": False,
            })
        events.sort(key=lambda e: (-e["severity"], -(e["magnitude"] or 0)))
        return json.dumps(events[:max_results], indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "simulated": True,
                           "message": "USGS feed unreachable — simulated data shown."})


@tool
def fetch_natural_events(categories: Optional[str] = None, max_results: int = 30) -> str:
    """
    Fetch open natural hazard events from NASA EONET (Earth Observatory Natural Event Tracker).
    Returns a JSON list of events including wildfires, storms, volcanoes, floods, droughts and ice events.
    Each entry contains: id, title, category, latitude, longitude, severity (0-4), time_utc,
    magnitude, unit, source.
    Falls back with a message if the feed is unreachable.

    Args:
        categories: Comma-separated category filter e.g. 'wildfire,storm'. None = all.
        max_results: Maximum number of results to return (default 30).
    """
    try:
        data = _safe_fetch("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=250")
        filter_cats = {c.strip().lower() for c in categories.split(",")} if categories else set()
        events = []
        for ev in data.get("events", []):
            cid = (ev.get("categories") or [{}])[0].get("id", "")
            cat = _EONET_MAP.get(cid, "other")
            if filter_cats and cat not in filter_cats:
                continue
            gs = ev.get("geometry", [])
            if not gs:
                continue
            g = gs[-1]
            coords = g.get("coordinates", [])
            # flatten polygon / point
            pts = []
            def _walk(c):
                if c and isinstance(c[0], (int, float)):
                    pts.append(c)
                elif c:
                    for x in c:
                        _walk(x)
            _walk(coords)
            if not pts:
                continue
            lon_c = sum(p[0] for p in pts) / len(pts)
            lat_c = sum(p[1] for p in pts) / len(pts)
            mag_val = g.get("magnitudeValue")
            unit_val = g.get("magnitudeUnit") or ""
            sev = _eonet_severity(cat, mag_val, unit_val)
            events.append({
                "id": ev.get("id", ""),
                "title": ev.get("title", ""),
                "category": cat,
                "category_label": _CATS.get(cat, "Other"),
                "latitude": round(lat_c, 4),
                "longitude": round(lon_c, 4),
                "severity": sev,
                "severity_label": _SEV_NAME[sev],
                "time_utc": g.get("date", ""),
                "magnitude": round(float(mag_val), 2) if mag_val is not None else None,
                "unit": unit_val,
                "source": "NASA EONET (live)",
                "simulated": False,
            })
        events.sort(key=lambda e: -e["severity"])
        return json.dumps(events[:max_results], indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "simulated": True,
                           "message": "NASA EONET feed unreachable."})


@tool
def fetch_weather_cities(city_names: Optional[str] = None) -> str:
    """
    Fetch current weather and air quality for the 12 UM_Terra Sentinel cities
    (or a subset) from Open-Meteo.
    Returns temperature (°C), wind speed, wind gusts, precipitation (mm/hr),
    weather code, and US AQI for each city.
    Falls back to an error message if unreachable.

    Args:
        city_names: Comma-separated city names to query, e.g. 'Tokyo,London'.
                    Default: all 12 sentinel cities.
    """
    if city_names:
        names = {n.strip().lower() for n in city_names.split(",")}
        cities = [c for c in SENTINEL_CITIES if c["n"].lower() in names]
        if not cities:
            return json.dumps({"error": "No matching sentinel cities found.",
                               "available": [c["n"] for c in SENTINEL_CITIES]})
    else:
        cities = SENTINEL_CITIES

    la = ",".join(str(c["lat"]) for c in cities)
    lo = ",".join(str(c["lon"]) for c in cities)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={la}&longitude={lo}"
        f"&current=temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation,weather_code"
        f"&daily=temperature_2m_max,wind_gusts_10m_max,precipitation_sum"
        f"&forecast_days=8&timezone=UTC&wind_speed_unit=kmh"
    )
    try:
        weather_data = _safe_fetch(url)
    except Exception as exc:
        return json.dumps({"error": str(exc), "message": "Open-Meteo weather feed unreachable."})

    try:
        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={la}&longitude={lo}&current=us_aqi"
        )
        aqi_data = _safe_fetch(aqi_url)
    except Exception:
        aqi_data = None

    wa = weather_data if isinstance(weather_data, list) else [weather_data]
    aa = (aqi_data if isinstance(aqi_data, list) else [aqi_data]) if aqi_data else []

    results = []
    for i, city in enumerate(cities):
        cur = wa[i].get("current", {}) if i < len(wa) else {}
        aqi_cur = aa[i].get("current", {}) if i < len(aa) else {}
        results.append({
            "city": city["n"],
            "latitude": city["lat"],
            "longitude": city["lon"],
            "temperature_c": cur.get("temperature_2m"),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
            "wind_gusts_kmh": cur.get("wind_gusts_10m"),
            "precipitation_mm": cur.get("precipitation"),
            "weather_code": cur.get("weather_code"),
            "us_aqi": aqi_cur.get("us_aqi"),
            "source": "Open-Meteo (live)",
            "simulated": False,
        })
    return json.dumps(results, indent=2)


@tool
def fetch_space_weather() -> str:
    """
    Fetch the latest planetary geomagnetic K-index (Kp) values from NOAA SWPC.
    Returns the current Kp index, G-storm level (if applicable), and the last
    24 historical 3-hour Kp readings.
    Kp ≥ 5 = geomagnetic storm. G1=5, G2=6, G3=7, G4=8, G5=9.
    Falls back to simulated data if the feed is unreachable.
    """
    try:
        raw = _safe_fetch("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json")
        rows = raw[1:] if (raw and isinstance(raw[0], list) and
                           isinstance(raw[0][0], str) and
                           not raw[0][0][0].isdigit()) else raw
        hist = []
        for r in rows[-24:]:
            if isinstance(r, list):
                t_str, kp_str = r[0], r[1]
            else:
                t_str = r.get("time_tag", "")
                kp_str = r.get("Kp") or r.get("kp_index") or r.get("estimated_kp")
            try:
                kp_val = float(kp_str)
                hist.append({"time_utc": t_str, "kp": round(kp_val, 2)})
            except (TypeError, ValueError):
                continue
        if not hist:
            raise ValueError("Empty or unparseable Kp response")
        current_kp = hist[-1]["kp"]
        g_level = None
        if current_kp >= 5:
            g_level = f"G{min(5, int(current_kp) - 4)}"
        return json.dumps({
            "current_kp": current_kp,
            "g_storm_level": g_level,
            "condition": (
                "G" + str(min(5, int(current_kp) - 4)) + " Geomagnetic Storm"
                if current_kp >= 5 else
                "Active" if current_kp >= 4 else "Quiet"
            ),
            "hf_radio_impact": current_kp >= 5,
            "gnss_impact": current_kp >= 6,
            "history_24h": hist,
            "source": "NOAA SWPC (live)",
            "simulated": False,
        }, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "simulated": True,
                           "message": "NOAA SWPC feed unreachable."})


@tool
def fetch_iss_position() -> str:
    """
    Fetch the current live position of the International Space Station (ISS)
    from wheretheiss.at.
    Returns latitude, longitude, altitude (km), velocity (km/h), and visibility.
    """
    try:
        data = _safe_fetch("https://api.wheretheiss.at/v1/satellites/25544")
        lat = float(data.get("latitude", 0))
        lon = float(data.get("longitude", 0))
        alt = float(data.get("altitude", 420))
        vel = float(data.get("velocity", 0))
        vis = data.get("visibility", "unknown")
        return json.dumps({
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "altitude_km": round(alt, 1),
            "velocity_kmh": round(vel, 1),
            "visibility": vis,
            "footprint_km": round(float(data.get("footprint", 0)), 1),
            "solar_lat": round(float(data.get("solar_lat", 0)), 2),
            "solar_lon": round(float(data.get("solar_lon", 0)), 2),
            "source": "wheretheiss.at (live)",
            "simulated": False,
        }, indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "simulated": True,
                           "message": "ISS position feed unreachable."})


@tool
def fetch_near_earth_objects(max_results: int = 10) -> str:
    """
    Fetch today's near-Earth object (NEO / asteroid) close approaches from NASA NeoWs.
    Returns a list sorted by miss distance (closest first), with name, estimated
    diameter (m), miss distance (lunar distances), velocity (km/s), and potentially
    hazardous asteroid (PHA) flag.
    Falls back to a message if unreachable (DEMO_KEY rate limits apply).

    Args:
        max_results: Maximum number of NEOs to return (default 10).
    """
    try:
        data = _safe_fetch(
            "https://api.nasa.gov/neo/rest/v1/feed/today?detailed=false&api_key=DEMO_KEY"
        )
        neos_raw = data.get("near_earth_objects", {})
        neos = []
        for date_key, items in neos_raw.items():
            for obj in items:
                approach = (obj.get("close_approach_data") or [{}])[0]
                dia = obj.get("estimated_diameter", {}).get("meters", {})
                neos.append({
                    "name": obj.get("name", "").strip("()"),
                    "potentially_hazardous": bool(obj.get("is_potentially_hazardous_asteroid")),
                    "diameter_m_max": dia.get("estimated_diameter_max"),
                    "miss_distance_lunar": approach.get("miss_distance", {}).get("lunar"),
                    "miss_distance_km": approach.get("miss_distance", {}).get("kilometers"),
                    "velocity_km_s": approach.get("relative_velocity", {})
                                               .get("kilometers_per_second"),
                    "close_approach_date": approach.get("close_approach_date_full", ""),
                    "source": "NASA NeoWs (live)",
                    "simulated": False,
                })
        neos.sort(key=lambda n: float(n["miss_distance_lunar"] or 9999))
        return json.dumps(neos[:max_results], indent=2)
    except Exception as exc:
        return json.dumps({"error": str(exc), "simulated": True,
                           "message": "NASA NeoWs feed unreachable (DEMO_KEY may be rate-limited)."})


@tool
def get_threat_index() -> str:
    """
    Compute the UM_Terra Sentinel global threat index (0–100) from current live
    earthquake and natural-event data combined with space-weather conditions.
    Returns the numeric score and textual level: NOMINAL (<20), ELEVATED (20-39),
    HIGH (40-64), SEVERE (≥65).
    This mirrors the exact threat formula used in the UM_Terra Sentinel console.
    """
    score = 0.0
    weights = [0.2, 1.0, 3.0, 8.0, 18.0]
    now_ms = time.time() * 1000
    messages = []

    # Earthquakes
    try:
        eq_raw = json.loads(fetch_earthquakes.invoke({"min_magnitude": 2.5, "max_results": 100}))
        if isinstance(eq_raw, list):
            for e in eq_raw:
                age_h = max(0, (now_ms - (
                    datetime.fromisoformat(
                        e["time_utc"].replace("Z", "+00:00")
                    ).timestamp() * 1000
                    if e.get("time_utc") else now_ms
                )) / 3_600_000)
                if 0 <= age_h <= 72:
                    score += weights[e.get("severity", 0)] * math.exp(-age_h / 18)
    except Exception as exc:
        messages.append(f"Earthquake data unavailable: {exc}")

    # Natural events
    try:
        ev_raw = json.loads(fetch_natural_events.invoke({"max_results": 200}))
        if isinstance(ev_raw, list):
            for e in ev_raw:
                score += weights[e.get("severity", 0)] * 0.5  # events lack precise timestamps
    except Exception as exc:
        messages.append(f"Natural events data unavailable: {exc}")

    # Space weather
    try:
        sw_raw = json.loads(fetch_space_weather.invoke({}))
        kp = sw_raw.get("current_kp")
        if kp and kp >= 5:
            score += (kp - 4) * 4
    except Exception as exc:
        messages.append(f"Space weather data unavailable: {exc}")

    v = round(100 * (1 - math.exp(-score / 60)))
    level = "NOMINAL" if v < 20 else "ELEVATED" if v < 40 else "HIGH" if v < 65 else "SEVERE"
    color = "#3ddc97" if v < 20 else "#ffc857" if v < 40 else "#ff8a3d" if v < 65 else "#ff4d5e"

    return json.dumps({
        "threat_index": v,
        "level": level,
        "color_hex": color,
        "raw_score": round(score, 2),
        "warnings": messages,
    }, indent=2)


@tool
def get_active_alarms() -> str:
    """
    Evaluate the UM_Terra Sentinel alarm conditions against live data and return
    a list of currently active alarm conditions, each with severity, kind, title
    and detail.  Severity levels: 1=ADVISORY, 2=WATCH, 3=WARNING, 4=CRITICAL.
    Checks: large earthquakes, wildfire clusters, severe storms, volcanoes,
    geomagnetic storms, extreme heat (≥42°C), damaging winds (≥70 km/h gusts),
    heavy rain (≥15 mm/hr), unhealthy AQI (≥150).
    """
    alarms = []
    # Thresholds (mirrors AL.cfg defaults in the console)
    QUAKE_MIN    = 5.0
    FIRE_CLUSTER = 6
    KP_MIN       = 5
    WIND_MIN     = 70    # km/h gusts
    TEMP_MIN     = 42    # °C
    AQI_MIN      = 150
    PRECIP_MIN   = 15    # mm/hr

    # ── Earthquakes ──────────────────────────────────────────────────────────
    try:
        eq_raw = json.loads(fetch_earthquakes.invoke({"min_magnitude": QUAKE_MIN, "max_results": 50}))
        if isinstance(eq_raw, list):
            for e in eq_raw:
                mag = e.get("magnitude", 0) or 0
                if mag >= QUAKE_MIN:
                    alarms.append({
                        "severity": max(2, e.get("severity", 2)),
                        "severity_label": _SEV_NAME[max(2, e.get("severity", 2))],
                        "kind": "Earthquake",
                        "title": f"M{mag:.1f} earthquake — {e.get('title', '')}",
                        "detail": (f"Depth {e.get('depth_km', '?')} km"
                                   + (" · TSUNAMI FLAG" if e.get("tsunami_flag") else "")),
                        "latitude": e.get("latitude"),
                        "longitude": e.get("longitude"),
                        "simulated": e.get("simulated", False),
                    })
    except Exception:
        pass

    # ── Natural events ────────────────────────────────────────────────────────
    try:
        ev_raw = json.loads(fetch_natural_events.invoke({"max_results": 200}))
        if isinstance(ev_raw, list):
            # Storms sev ≥ 3
            for e in ev_raw:
                if e.get("category") == "storm" and e.get("severity", 0) >= 3:
                    alarms.append({
                        "severity": e["severity"],
                        "severity_label": _SEV_NAME[e["severity"]],
                        "kind": "Storm",
                        "title": e.get("title", "Severe storm system"),
                        "detail": f"Intensity {e.get('magnitude', '?')} {e.get('unit', '')}".strip(),
                        "latitude": e.get("latitude"),
                        "longitude": e.get("longitude"),
                        "simulated": e.get("simulated", False),
                    })
                elif e.get("category") == "volcano":
                    alarms.append({
                        "severity": 2,
                        "severity_label": _SEV_NAME[2],
                        "kind": "Volcano",
                        "title": e.get("title", "Volcanic activity"),
                        "detail": "Open volcanic activity reported",
                        "latitude": e.get("latitude"),
                        "longitude": e.get("longitude"),
                        "simulated": e.get("simulated", False),
                    })
            # Wildfire cluster detection (10° grid cells)
            cells: dict = {}
            for e in ev_raw:
                if e.get("category") == "wildfire":
                    lat, lon = e.get("latitude", 0), e.get("longitude", 0)
                    k = f"{int((lat + 90) / 10)}:{int((lon + 180) / 10)}"
                    cells.setdefault(k, []).append(e)
            for k, fires in cells.items():
                if len(fires) >= FIRE_CLUSTER:
                    la = sum(f["latitude"] for f in fires) / len(fires)
                    lo = sum(f["longitude"] for f in fires) / len(fires)
                    alarms.append({
                        "severity": 3 if len(fires) >= FIRE_CLUSTER * 2 else 2,
                        "severity_label": _SEV_NAME[3 if len(fires) >= FIRE_CLUSTER * 2 else 2],
                        "kind": "Wildfire Cluster",
                        "title": f"Wildfire cluster · {len(fires)} active fires",
                        "detail": f"10° grid cell near {la:.1f}°, {lo:.1f}°",
                        "latitude": la,
                        "longitude": lo,
                        "simulated": False,
                    })
    except Exception:
        pass

    # ── Space weather ─────────────────────────────────────────────────────────
    try:
        sw_raw = json.loads(fetch_space_weather.invoke({}))
        kp = sw_raw.get("current_kp")
        if kp and kp >= KP_MIN:
            sev = 4 if kp >= 7 else 3 if kp >= 6 else 2
            alarms.append({
                "severity": sev,
                "severity_label": _SEV_NAME[sev],
                "kind": "Space Weather",
                "title": f"Geomagnetic storm G{min(5, int(kp) - 4)} · Kp {kp:.1f}",
                "detail": "HF radio, GNSS and power grid effects possible",
                "latitude": None,
                "longitude": None,
                "simulated": sw_raw.get("simulated", False),
            })
    except Exception:
        pass

    # ── City weather alarms ───────────────────────────────────────────────────
    try:
        wx_raw = json.loads(fetch_weather_cities.invoke({}))
        if isinstance(wx_raw, list):
            for c in wx_raw:
                gust = c.get("wind_gusts_kmh") or 0
                temp = c.get("temperature_c")
                precip = c.get("precipitation_mm") or 0
                aqi = c.get("us_aqi")
                city = c.get("city", "")
                if gust >= WIND_MIN:
                    sev = 3 if gust >= WIND_MIN + 25 else 2
                    alarms.append({
                        "severity": sev, "severity_label": _SEV_NAME[sev],
                        "kind": "Weather",
                        "title": f"Damaging wind · {city}",
                        "detail": f"Gusts {gust:.0f} km/h",
                        "latitude": c.get("latitude"), "longitude": c.get("longitude"),
                        "simulated": c.get("simulated", False),
                    })
                if temp is not None and temp >= TEMP_MIN:
                    sev = 3 if temp >= TEMP_MIN + 4 else 2
                    alarms.append({
                        "severity": sev, "severity_label": _SEV_NAME[sev],
                        "kind": "Extreme Heat",
                        "title": f"Extreme heat · {city}",
                        "detail": f"{temp:.1f} °C at surface",
                        "latitude": c.get("latitude"), "longitude": c.get("longitude"),
                        "simulated": c.get("simulated", False),
                    })
                if precip >= PRECIP_MIN:
                    alarms.append({
                        "severity": 2, "severity_label": _SEV_NAME[2],
                        "kind": "Heavy Rain",
                        "title": f"Heavy precipitation · {city}",
                        "detail": f"{precip:.1f} mm in last hour",
                        "latitude": c.get("latitude"), "longitude": c.get("longitude"),
                        "simulated": c.get("simulated", False),
                    })
                if aqi is not None and aqi >= AQI_MIN:
                    sev = 4 if aqi >= 300 else 3 if aqi >= 200 else 2
                    alarms.append({
                        "severity": sev, "severity_label": _SEV_NAME[sev],
                        "kind": "Air Quality",
                        "title": f"Unhealthy air · {city}",
                        "detail": f"US AQI {aqi:.0f}",
                        "latitude": c.get("latitude"), "longitude": c.get("longitude"),
                        "simulated": c.get("simulated", False),
                    })
    except Exception:
        pass

    alarms.sort(key=lambda a: -a["severity"])
    return json.dumps({
        "active_alarms": alarms,
        "total": len(alarms),
        "critical": sum(1 for a in alarms if a["severity"] >= 4),
        "warning": sum(1 for a in alarms if a["severity"] == 3),
        "watch": sum(1 for a in alarms if a["severity"] == 2),
        "advisory": sum(1 for a in alarms if a["severity"] == 1),
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, indent=2)


@tool
def get_sentinel_summary() -> str:
    """
    Generate a full UM_Terra Sentinel situation report: threat index, active
    alarms, top priority signals, space weather, ISS position, sentinel city
    conditions and near-Earth objects. Suitable for the Newsroom / SITREP tab.
    Returns a rich structured JSON summary with all key intelligence domains.
    © 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.
    """
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "product": "UM_Terra Sentinel — Planetary Intelligence Network",
        "copyright": "© 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com · All rights reserved.",
        "generated_utc": now_utc,
        "domains": {},
    }

    # Threat index
    try:
        report["domains"]["threat_index"] = json.loads(get_threat_index.invoke({}))
    except Exception as exc:
        report["domains"]["threat_index"] = {"error": str(exc)}

    # Alarms
    try:
        report["domains"]["alarms"] = json.loads(get_active_alarms.invoke({}))
    except Exception as exc:
        report["domains"]["alarms"] = {"error": str(exc)}

    # Top earthquakes
    try:
        report["domains"]["earthquakes"] = json.loads(
            fetch_earthquakes.invoke({"min_magnitude": 4.5, "max_results": 6})
        )
    except Exception as exc:
        report["domains"]["earthquakes"] = {"error": str(exc)}

    # Natural events (top by severity)
    try:
        evs = json.loads(fetch_natural_events.invoke({"max_results": 8}))
        report["domains"]["natural_events"] = evs
    except Exception as exc:
        report["domains"]["natural_events"] = {"error": str(exc)}

    # Space weather
    try:
        sw = json.loads(fetch_space_weather.invoke({}))
        report["domains"]["space_weather"] = {
            k: sw[k] for k in ("current_kp", "g_storm_level", "condition",
                                "hf_radio_impact", "gnss_impact", "simulated")
            if k in sw
        }
    except Exception as exc:
        report["domains"]["space_weather"] = {"error": str(exc)}

    # ISS
    try:
        report["domains"]["iss"] = json.loads(fetch_iss_position.invoke({}))
    except Exception as exc:
        report["domains"]["iss"] = {"error": str(exc)}

    # City watch (top concerns)
    try:
        wx = json.loads(fetch_weather_cities.invoke({}))
        if isinstance(wx, list):
            # Hottest, windiest, worst AQI
            wx_sorted_temp = sorted(wx, key=lambda c: c.get("temperature_c") or -999, reverse=True)
            wx_sorted_wind = sorted(wx, key=lambda c: c.get("wind_gusts_kmh") or 0, reverse=True)
            wx_sorted_aqi  = sorted(wx, key=lambda c: c.get("us_aqi") or 0, reverse=True)
            report["domains"]["sentinel_cities"] = {
                "hottest": wx_sorted_temp[0] if wx_sorted_temp else None,
                "windiest_gusts": wx_sorted_wind[0] if wx_sorted_wind else None,
                "worst_aqi": wx_sorted_aqi[0] if wx_sorted_aqi else None,
                "all": wx,
            }
    except Exception as exc:
        report["domains"]["sentinel_cities"] = {"error": str(exc)}

    # NEOs
    try:
        neos = json.loads(fetch_near_earth_objects.invoke({"max_results": 5}))
        report["domains"]["near_earth_objects"] = neos
    except Exception as exc:
        report["domains"]["near_earth_objects"] = {"error": str(exc)}

    return json.dumps(report, indent=2)


# Expose all tools as a list for the factory
ALL_TOOLS = [
    fetch_earthquakes,
    fetch_natural_events,
    fetch_weather_cities,
    fetch_space_weather,
    fetch_iss_position,
    fetch_near_earth_objects,
    get_threat_index,
    get_active_alarms,
    get_sentinel_summary,
]
