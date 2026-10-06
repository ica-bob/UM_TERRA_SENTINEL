"""
UM_TERRA_SENTINEL Agent — LangGraph agent definition.
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.

Extends BaseLangGraphAgent from aicoe-agent-utils.
"""
from aicoe_agent_utils.agents.base_langgraph_agent import BaseLangGraphAgent
from a2a.types import AgentCard, AgentCapabilities, AgentSkill

from tools import ALL_TOOLS


class UMTerraSentinelAgent(BaseLangGraphAgent):
    """
    UM_TERRA_SENTINEL — Planetary Intelligence Network Agent.

    Provides natural-language access to the full UM_Terra Sentinel intelligence
    stack: live earthquakes, natural hazards, weather, space weather, ISS
    tracking, near-Earth objects, alarm evaluation and situation reports.

    © 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.
    """

    # ── Framework hooks ───────────────────────────────────────────────────────

    def get_prompt(self) -> str:
        return (
            "You are UM_TERRA_SENTINEL, the AI backbone of the UM_Terra Sentinel "
            "Planetary Intelligence Network — a live Earth intelligence console "
            "designed and owned by Utsav Mukherjee "
            "(© 2026, utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com). "
            "All rights reserved.\n\n"
            "Your mission is to provide accurate, real-time Earth intelligence by calling "
            "the available tools and synthesising the results into clear, operator-ready "
            "answers. You cover:\n"
            "  • Seismic events (USGS earthquakes)\n"
            "  • Natural hazards (NASA EONET: wildfires, storms, volcanoes, floods, drought, ice)\n"
            "  • Weather & air quality for 12 sentinel cities (Open-Meteo)\n"
            "  • Space weather — Kp index, G-storm levels (NOAA SWPC)\n"
            "  • International Space Station live position (wheretheiss.at)\n"
            "  • Near-Earth objects / asteroid close approaches (NASA NeoWs)\n"
            "  • Global threat index (composite 0–100 score: NOMINAL / ELEVATED / HIGH / SEVERE)\n"
            "  • Active alarm evaluation (earthquake, wildfire, storm, volcano, "
            "    geomagnetic storm, extreme heat, damaging wind, heavy rain, AQI)\n"
            "  • Full situation report generation (Newsroom / SITREP)\n\n"
            "Guidelines:\n"
            "- Always call the relevant tool(s) before answering factual questions.\n"
            "- When data is simulated (feed unreachable), clearly state 'SIMULATED DATA' "
            "  in your answer.\n"
            "- Express severity using the console levels: MINOR, ADVISORY, WATCH, WARNING, CRITICAL.\n"
            "- For alarm queries, list all active conditions sorted by severity (highest first).\n"
            "- When asked for a situation report, call get_sentinel_summary and present the "
            "  findings in a structured, readable format.\n"
            "- You are not an official warning service. Always advise users to follow their "
            "  national civil-protection and meteorological authorities for safety decisions.\n"
            "- Do not disclose internal implementation details beyond what is needed to answer.\n"
            "- Copyright and attribution notices must always be preserved in reports.\n"
        )

    def get_agent_card(self) -> AgentCard:
        return AgentCard(
            name="UM_TERRA_SENTINEL",
            description=(
                "UM_Terra Sentinel — Planetary Intelligence Network. "
                "Live Earth intelligence console agent providing real-time data on "
                "earthquakes, natural hazards, weather & air quality for 12 sentinel cities, "
                "space weather (Kp index), ISS live position, near-Earth objects, "
                "global threat index computation and alarm evaluation. "
                "© 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com."
            ),
            version="2026.10.05-R1",
            url="",
            capabilities=AgentCapabilities(streaming=True),
            skills=[
                AgentSkill(
                    id="live_earthquakes",
                    name="Live Earthquakes",
                    description="Fetch real-time earthquake data from USGS (M≥2.5, past 24 h).",
                    examples=["What are the latest earthquakes?",
                              "Show me all M5+ earthquakes today.",
                              "Were there any tsunamigenic earthquakes recently?"],
                ),
                AgentSkill(
                    id="natural_hazards",
                    name="Natural Hazards",
                    description="Track open wildfires, storms, volcanoes, floods and drought from NASA EONET.",
                    examples=["List active wildfires worldwide.",
                              "Are there any Category 4+ hurricanes right now?",
                              "Which volcanoes are currently active?"],
                ),
                AgentSkill(
                    id="weather_cities",
                    name="Sentinel City Weather",
                    description="Current temperature, wind, precipitation and air quality for 12 global cities.",
                    examples=["What is the weather in Tokyo right now?",
                              "Which sentinel city has the worst air quality?",
                              "Is there extreme heat anywhere in the sentinel network?"],
                ),
                AgentSkill(
                    id="space_weather",
                    name="Space Weather",
                    description="NOAA Kp index, G-storm levels and impacts on HF radio and GNSS.",
                    examples=["What is the current Kp index?",
                              "Is there a geomagnetic storm right now?",
                              "Will space weather affect GPS today?"],
                ),
                AgentSkill(
                    id="iss_tracking",
                    name="ISS Live Tracking",
                    description="Real-time ISS latitude, longitude, altitude and velocity.",
                    examples=["Where is the ISS right now?",
                              "What altitude is the International Space Station at?"],
                ),
                AgentSkill(
                    id="near_earth_objects",
                    name="Near-Earth Objects",
                    description="Today's asteroid close approaches from NASA NeoWs, sorted by miss distance.",
                    examples=["Are any asteroids passing close to Earth today?",
                              "What is the closest near-Earth object this week?",
                              "List potentially hazardous asteroids approaching Earth."],
                ),
                AgentSkill(
                    id="threat_index",
                    name="Global Threat Index",
                    description="Compute the composite 0–100 threat score across all intelligence domains.",
                    examples=["What is the current global threat index?",
                              "Is the threat level elevated right now?"],
                ),
                AgentSkill(
                    id="alarm_engine",
                    name="Alarm Engine",
                    description=(
                        "Evaluate all alarm conditions (earthquake, wildfire cluster, severe storm, "
                        "volcano, geomagnetic storm, extreme heat, damaging wind, heavy rain, AQI) "
                        "and return active alarms sorted by severity."
                    ),
                    examples=["What alarms are active right now?",
                              "Are there any critical alerts?",
                              "Show me all WARNING-level conditions."],
                ),
                AgentSkill(
                    id="situation_report",
                    name="Situation Report",
                    description=(
                        "Generate a full UM_Terra Sentinel SITREP covering all intelligence "
                        "domains: threat index, alarms, earthquakes, hazards, space weather, "
                        "ISS, city weather and NEOs."
                    ),
                    examples=["Generate a full situation report.",
                              "Give me the current SITREP.",
                              "What is the global intelligence summary right now?"],
                ),
            ],
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
        )

    def get_looking_up_info_msg(self) -> str:
        return "🌍 UM_TERRA_SENTINEL — Querying live Earth intelligence feeds…"

    def get_processing_info_msg(self) -> str:
        return "⚡ UM_TERRA_SENTINEL — Processing planetary data…"
