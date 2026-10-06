"""
UM_TERRA_SENTINEL Agent — Server entry point.
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.

Usage:
    python main.py [--host HOST] [--port PORT] [--public-host URL]
"""
import asyncio
import asyncclick as click

import config
from a2a_factory import UMTerraSentinelFactory

try:
    from aicoe_agent_utils.utils import start_a2a_server
except ImportError as exc:
    raise ImportError(
        "aicoe-agent-utils is not installed. "
        "Run: pip install -r requirements.txt"
    ) from exc


@click.command()
@click.option("--host",        default=config.DEFAULT_HOST,        show_default=True, help="Bind host")
@click.option("--port",        default=config.DEFAULT_PORT,        show_default=True, help="Bind port", type=int)
@click.option("--public-host", default=config.DEFAULT_PUBLIC_HOST, show_default=True, help="Public base URL (optional)")
async def main(host: str, port: int, public_host: str) -> None:
    """
    Start the UM_TERRA_SENTINEL A2A agent server.

    © 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.
    """
    # Optional: AgentOps observability
    if config.ENABLE_AGENTOPS:
        try:
            import agentops
            init_kwargs = {"app_name": config.AGENTOPS_APP_NAME}
            if config.AGENTOPS_ENDPOINT:
                init_kwargs["endpoint"] = config.AGENTOPS_ENDPOINT
            agentops.init(**init_kwargs)
            print("[UM_TERRA_SENTINEL] AgentOps observability enabled.")
        except ImportError:
            print("[UM_TERRA_SENTINEL] WARNING: ENABLE_AGENTOPS=true but agentops not installed. "
                  "Run: pip install aicoe-agent-utils[agentops]")

    factory = UMTerraSentinelFactory(
        enable_client_auth=config.ENABLE_CLIENT_AUTH,
        enable_user_auth=config.ENABLE_USER_AUTH,
        ibm_tenant_id=config.IBM_TENANT_ID       if config.ENABLE_USER_AUTH else None,
        ibm_introspect_url=config.IBM_INTROSPECT_URL if config.ENABLE_USER_AUTH else None,
    )

    agent    = factory.make_agent()
    executor = factory.make_agent_executor(agent)

    agent_card = agent.get_agent_card()
    # Inject the runtime URL into the card
    base_url = public_host.rstrip("/") if public_host else f"http://{host}:{port}"
    agent_card.url = base_url

    print(
        f"\n"
        f"  ██╗   ██╗███╗   ███╗    ████████╗███████╗██████╗ ██████╗  █████╗ \n"
        f"  ██║   ██║████╗ ████║       ██╔══╝██╔════╝██╔══██╗██╔══██╗██╔══██╗\n"
        f"  ██║   ██║██╔████╔██║       ██║   █████╗  ██████╔╝██████╔╝███████║\n"
        f"  ██║   ██║██║╚██╔╝██║       ██║   ██╔══╝  ██╔══██╗██╔══██╗██╔══██║\n"
        f"  ╚██████╔╝██║ ╚═╝ ██║       ██║   ███████╗██║  ██║██║  ██║██║  ██║\n"
        f"   ╚═════╝ ╚═╝     ╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝\n"
        f"\n"
        f"  UM_TERRA_SENTINEL — Planetary Intelligence Network\n"
        f"  © 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.\n"
        f"\n"
        f"  Agent   : {agent_card.name}\n"
        f"  Version : {agent_card.version}\n"
        f"  LLM     : {config.LLM_PROVIDER} / {config.WATSONX_MODEL_ID if config.LLM_PROVIDER=='watsonx' else config.OLLAMA_MODEL_ID}\n"
        f"  Host    : {host}:{port}\n"
        f"  URL     : {base_url}\n"
        f"  Auth    : client={config.ENABLE_CLIENT_AUTH}  user={config.ENABLE_USER_AUTH}\n"
        f"  Tools   : 9 intelligence tools active\n"
    )

    await start_a2a_server(
        agent_executor=executor,
        agent_card=agent_card,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    asyncio.run(main())
