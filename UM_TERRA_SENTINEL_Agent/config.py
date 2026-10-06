"""
UM_TERRA_SENTINEL Agent — Configuration
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM Provider ──────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "watsonx")

# WatsonX
WATSONX_APIKEY       = os.getenv("WATSONX_APIKEY", "")
WATSONX_URL          = os.getenv("WATSONX_URL", "")
WATSONX_PROJECT_ID   = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_MODEL_ID     = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

# Ollama (alternative)
OLLAMA_BASE_URL  = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_ID  = os.getenv("OLLAMA_MODEL_ID", "llama3")

# ── MCP Servers ───────────────────────────────────────────────────────────────
# Comma-separated names / URLs for MCP tool servers to connect to.
# UM_Terra Sentinel uses:
#   - USGS Earthquake feed (HTTPS, no MCP needed, handled inline)
#   - NASA EONET           (HTTPS, inline)
#   - Open-Meteo           (HTTPS, inline)
#   - NOAA SWPC            (HTTPS, inline)
#   - wheretheiss.at       (HTTPS, inline)
#   - NASA NeoWs           (HTTPS, inline)
# Additional optional MCP servers can be wired in via env.
_raw_names = os.getenv("MCP_SERVER_NAMES", "")
_raw_urls  = os.getenv("MCP_SERVER_URLS",  "")

MCP_SERVER_NAMES     = [n.strip() for n in _raw_names.split(",") if n.strip()]
MCP_SERVER_URLS      = [u.strip() for u in _raw_urls.split(",")  if u.strip()]
MCP_SERVER_TRANSPORT = os.getenv("MCP_SERVER_TRANSPORT", "streamable-http")

# ── Agent Server ──────────────────────────────────────────────────────────────
DEFAULT_HOST        = os.getenv("DEFAULT_HOST",        "0.0.0.0")
DEFAULT_PORT        = int(os.getenv("DEFAULT_PORT",    "8080"))
DEFAULT_PUBLIC_HOST = os.getenv("DEFAULT_PUBLIC_HOST", "")

# ── Authentication (disabled by default) ─────────────────────────────────────
ENABLE_CLIENT_AUTH = os.getenv("ENABLE_CLIENT_AUTH", "false").lower() == "true"
ENABLE_USER_AUTH   = os.getenv("ENABLE_USER_AUTH",   "false").lower() == "true"
IBM_TENANT_ID      = os.getenv("IBM_TENANT_ID",      "")
IBM_INTROSPECT_URL = os.getenv("IBM_INTROSPECT_URL",  "")

# ── AgentOps Observability (disabled by default) ─────────────────────────────
ENABLE_AGENTOPS    = os.getenv("ENABLE_AGENTOPS",   "false").lower() == "true"
AGENTOPS_APP_NAME  = os.getenv("AGENTOPS_APP_NAME", "UM_TERRA_SENTINEL")
AGENTOPS_ENDPOINT  = os.getenv("AGENTOPS_ENDPOINT", "")

# ── Live data API base URLs ───────────────────────────────────────────────────
USGS_URL_DAY     = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
USGS_URL_MONTH   = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson"
EONET_URL        = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=250"
OPEN_METEO_URL   = "https://api.open-meteo.com/v1/forecast"
AQI_URL          = "https://air-quality-api.open-meteo.com/v1/air-quality"
NOAA_KP_URL      = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
ISS_URL          = "https://api.wheretheiss.at/v1/satellites/25544"
NEOWS_URL        = "https://api.nasa.gov/neo/rest/v1/feed/today?detailed=false&api_key=DEMO_KEY"
