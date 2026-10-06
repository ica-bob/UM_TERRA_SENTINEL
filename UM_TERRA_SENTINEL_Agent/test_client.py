"""
UM_TERRA_SENTINEL Agent — Test client.
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.

Runs a battery of test queries against the running agent server.
Usage:
    python test_client.py [--url http://localhost:8080]
"""
import asyncio
import asyncclick as click

try:
    from aicoe_agent_utils.a2a.client_utils import run_streaming_test
    from a2a.client import A2AClient
    import httpx
except ImportError as exc:
    raise ImportError(
        "aicoe-agent-utils / a2a SDK not installed. "
        "Run: pip install -r requirements.txt"
    ) from exc

# Test queries that exercise every intelligence skill
TEST_QUERIES = [
    # ── Situation report (calls get_sentinel_summary) ─────────────────────
    "Give me a full UM_Terra Sentinel situation report right now.",

    # ── Threat index ──────────────────────────────────────────────────────
    "What is the current global threat index?",

    # ── Earthquakes ───────────────────────────────────────────────────────
    "What are the latest significant earthquakes in the past 24 hours?",
    "Were there any M6+ earthquakes recently with a tsunami flag?",

    # ── Natural hazards ───────────────────────────────────────────────────
    "List all active wildfires currently tracked by NASA EONET.",
    "Are there any Category 3 or higher tropical storms active right now?",
    "Which volcanoes are currently showing open activity?",

    # ── Weather & AQI ─────────────────────────────────────────────────────
    "What is the weather like in Tokyo and Mumbai right now?",
    "Which of the sentinel cities has the worst air quality index today?",
    "Is there any extreme heat warning anywhere in the sentinel network?",

    # ── Space weather ─────────────────────────────────────────────────────
    "What is the current planetary Kp index and is there a geomagnetic storm?",
    "Could space weather affect GPS or HF radio communications today?",

    # ── ISS ───────────────────────────────────────────────────────────────
    "Where is the International Space Station right now?",

    # ── Near-Earth Objects ─────────────────────────────────────────────────
    "Are there any asteroids passing close to Earth today?",
    "List potentially hazardous asteroids approaching Earth this week.",

    # ── Alarms ────────────────────────────────────────────────────────────
    "What active alarms are currently triggered on the UM_Terra Sentinel console?",
    "Show me all CRITICAL and WARNING level conditions.",
]


@click.command()
@click.option("--url", default="http://localhost:8080",
              show_default=True, help="Agent server base URL")
@click.option("--query", default=None,
              help="Run a single custom query instead of the full test battery")
async def main(url: str, query: str) -> None:
    """
    Test client for UM_TERRA_SENTINEL agent.
    © 2026 Utsav Mukherjee · utsav.mukherjee@ibm.com · utsavmukherjee143@gmail.com.
    """
    async with httpx.AsyncClient(base_url=url, timeout=120.0) as http_client:
        client = A2AClient(httpx_client=http_client)

        queries = [query] if query else TEST_QUERIES

        print(
            f"\n{'='*70}\n"
            f"  UM_TERRA_SENTINEL — Test Client\n"
            f"  Server : {url}\n"
            f"  Queries: {len(queries)}\n"
            f"{'='*70}\n"
        )

        for i, q in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] QUERY: {q}")
            print("-" * 60)
            try:
                await run_streaming_test(client, q)
            except Exception as exc:
                print(f"  ERROR: {exc}")
            print()

        print(f"\n{'='*70}")
        print("  Test run complete.")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
