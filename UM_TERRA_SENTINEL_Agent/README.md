# UM_TERRA_SENTINEL Agent

**Planetary Intelligence Network — AI Agent**
© 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com · All rights reserved.

---

## Overview

`UM_TERRA_SENTINEL` is an A2A (Agent-to-Agent) compatible AI agent that provides
natural-language access to the full live Earth intelligence stack powering the
**UM_Terra Sentinel** browser console. It connects to all six live data sources used
by the console and exposes them through nine structured LangChain tools.

### Intelligence Domains

| Domain | Tool | Live Source |
|---|---|---|
| Seismic events | `fetch_earthquakes` | USGS GeoJSON Feed |
| Natural hazards | `fetch_natural_events` | NASA EONET v3 |
| Weather & AQI | `fetch_weather_cities` | Open-Meteo |
| Space weather | `fetch_space_weather` | NOAA SWPC |
| ISS tracking | `fetch_iss_position` | wheretheiss.at |
| Near-Earth objects | `fetch_near_earth_objects` | NASA NeoWs |
| Threat index | `get_threat_index` | Composite (all sources) |
| Alarm evaluation | `get_active_alarms` | Composite (all sources) |
| Situation report | `get_sentinel_summary` | All domains |

All tools validate outbound URLs against an allow-list of 7 trusted hosts
(matching the browser's Content-Security-Policy) and use HTTPS-only connections.
If a feed is unreachable, the tool returns a clear `"simulated": true` message.

---

## Project Structure

```
UM_TERRA_SENTINEL_Agent/
├── aicoe-agent-utils/          # Git submodule (framework)
├── main.py                     # Server entry point  ← run this
├── config.py                   # All configuration from env vars
├── um_terra_sentinel_agent.py  # Agent logic (extends BaseLangGraphAgent)
├── a2a_factory.py              # A2A factory (extends A2AAgentFactory)
├── tools.py                    # 9 intelligence tools (LangChain @tool)
├── test_client.py              # Test client (17 pre-built queries)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container (Red Hat UBI9 minimal, non-root)
├── .env.example                # Environment template
└── .gitmodules                 # Submodule config
```

---

## Quick Start

### 1 · Clone & initialise submodule

```bash
git submodule add https://github.ibm.com/AI-CoE/aicoe-agent-utils.git
git submodule update --init --recursive
```

### 2 · Create virtual environment & install

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3 · Configure

```bash
cp .env.example .env
# Edit .env — fill in WATSONX_APIKEY, WATSONX_URL, WATSONX_PROJECT_ID
```

### 4 · Run the agent server

```bash
python main.py
```

Server starts at `http://0.0.0.0:8080`.

### 5 · Test

```bash
python test_client.py
```

Runs 17 pre-built queries covering every intelligence domain.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `watsonx` | `watsonx` or `ollama` |
| `WATSONX_APIKEY` | — | WatsonX API key |
| `WATSONX_URL` | — | WatsonX ML endpoint |
| `WATSONX_PROJECT_ID` | — | WatsonX project ID |
| `WATSONX_MODEL_ID` | `meta-llama/llama-3-3-70b-instruct` | WatsonX model |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL_ID` | `llama3` | Ollama model |
| `DEFAULT_HOST` | `0.0.0.0` | Bind host |
| `DEFAULT_PORT` | `8080` | Bind port |
| `ENABLE_CLIENT_AUTH` | `false` | Client auth (requires IBM_TENANT_ID + IBM_INTROSPECT_URL) |
| `ENABLE_USER_AUTH` | `false` | User auth |
| `ENABLE_AGENTOPS` | `false` | AgentOps observability (install: `pip install aicoe-agent-utils[agentops]`) |

---

## Optional: Docker

```bash
docker build -t um-terra-sentinel-agent .
docker run --env-file .env -p 8080:8080 um-terra-sentinel-agent
```

---

## Alarm Thresholds (mirrors console defaults)

| Condition | Default Threshold |
|---|---|
| Earthquake | M ≥ 5.0 |
| Wildfire cluster | ≥ 6 fires in 10° grid cell |
| Geomagnetic storm | Kp ≥ 5 (G1+) |
| Wind gust | ≥ 70 km/h |
| Extreme heat | ≥ 42 °C |
| Heavy rain | ≥ 15 mm/hr |
| Air quality | US AQI ≥ 150 |

---

## Legal & Attribution

- **UM_Terra Sentinel** application, agent code and interface design:
  © 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com · All rights reserved.
- Third-party data remains property of its providers:  
  USGS · NASA EONET · Open-Meteo (CC BY 4.0) · NOAA SWPC · wheretheiss.at · NASA NeoWs
- This is an information display, not an official warning service.  
  Follow your national civil-protection and meteorological authorities for safety decisions.
