"""
UM_TERRA_SENTINEL Agent — A2A Factory.
© 2026 Utsav Mukherjee <utsav.mukherjee@ibm.com | utsavmukherjee143@gmail.com>. All rights reserved.
"""
from typing import Any

from aicoe_agent_utils.agents.a2a_agent_factory import A2AAgentFactory
from aicoe_agent_utils.agents.base_langgraph_agent import BaseLangGraphAgent
from aicoe_agent_utils.agents.base_agent_executor import BaseAgentExecutor
from aicoe_agent_utils.agents.langgraph_agent_executor import LangGraphAgentExecutor

from um_terra_sentinel_agent import UMTerraSentinelAgent
from tools import ALL_TOOLS
import config


class UMTerraSentinelFactory(A2AAgentFactory):
    """
    Factory that wires the UM_TERRA_SENTINEL agent to the A2A server.
    Handles LLM selection (WatsonX / Ollama) and tool injection.
    """

    def make_agent(self) -> BaseLangGraphAgent:
        llm = self._build_llm()
        agent = UMTerraSentinelAgent(
            llm=llm,
            tools=ALL_TOOLS,
        )
        return agent

    def make_agent_executor(self, agent: BaseLangGraphAgent) -> BaseAgentExecutor:
        return LangGraphAgentExecutor(agent=agent)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_llm(self) -> Any:
        """Return a LangChain LLM bound to the configured provider."""
        provider = config.LLM_PROVIDER.lower()

        if provider == "watsonx":
            from langchain_ibm import ChatWatsonx
            return ChatWatsonx(
                model_id=config.WATSONX_MODEL_ID,
                url=config.WATSONX_URL,
                apikey=config.WATSONX_APIKEY,
                project_id=config.WATSONX_PROJECT_ID,
                params={
                    "max_new_tokens": 4096,
                    "temperature": 0.1,
                },
            )

        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.OLLAMA_MODEL_ID,
                base_url=config.OLLAMA_BASE_URL,
                temperature=0.1,
            )

        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. "
            "Supported values: 'watsonx', 'ollama'."
        )
