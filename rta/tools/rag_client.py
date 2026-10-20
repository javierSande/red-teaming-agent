from typing import Any, Dict, List
from urllib.parse import urljoin

import requests


class RAGClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        if not base_url or not base_url.strip():
            raise ValueError("base_url must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        """Return the RAG service health payload."""
        response = requests.get(
            urljoin(self.base_url, "health"),
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("RAG health response must be a JSON object")
        return payload

    def query(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the RAG model with a given input string and return the top_k results.

        :param query: The input query string.
        :param top_k: The number of top results to return.
        :return: A list of dictionaries containing the results.
        """
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= top_k <= 100:
            raise ValueError("top_k must be between 1 and 100")

        response = requests.post(
            urljoin(self.base_url, "query"),
            json={"query": query, "top_k": top_k},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("retrieved_documents")
        if not isinstance(results, list):
            raise ValueError("RAG response is missing a retrieved_documents list")
        return results