from typing import Any, Dict, List, Optional

from rta.agents.retrieval_agent import InformationRetrievalAgent
from rta.tools.rag_client import RAGClient
from rta.cli.config import CONFIG


class LocalRtaClient:
    """Temporary in-process client retained for development before the RTA API exists."""

    def __init__(self, rag_url: str, ollama_host: Optional[str] = None):
        self.rag_client = RAGClient(rag_url)
        self.ollama_host = ollama_host
        self._agents = {
            "retrieval": self._create_retrieval_agent,
        }

    def health(self) -> Dict[str, Any]:
        return self.rag_client.health()

    def agents(self) -> List[str]:
        return sorted(self._agents)

    def run(self, agent: str, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        if agent not in self._agents:
            raise ValueError(f"unknown agent: {agent}")
        if top_k is None:
            top_k = CONFIG["cli"]["top_k"]
        return self._agents[agent]().run(query, top_k=top_k)

    def _create_retrieval_agent(self) -> InformationRetrievalAgent:
        return InformationRetrievalAgent(
            self.rag_client,
            ollama_host=self.ollama_host or "",
        )
