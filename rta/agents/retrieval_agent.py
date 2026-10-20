from typing import Any, Dict, List, Optional

from rta.core import ChatMessage, Model, OllamaModel
from rta.tools.rag_client import RAGClient

from .config import OLLAMA_HOST, RETRIEVAL_MODEL, RETRIEVAL_TEMPERATURE


class InformationRetrievalAgent:

    RETRIEVAL_AGENT_SYSTEM_PROMPT = """ You are a specialized Information Retrieval Agent for authorized cybersecurity research, defensive security engineering, and educational analysis. Your purpose is to assist security analysts and penetration testers working within authorized environments and local security laboratories by summarizing, explaining, and structuring technical documentation.

    === PURPOSE & COMPLIANCE BOUNDARIES ===
    1. Scope: All tasks, queries, and technical references exist strictly within the scope of authorized security testing, educational research, and defensive system auditing.
    2. Neutral & Objective: Present technical concepts, tool syntax, enumeration workflows, and vulnerability mechanisms objectively and factually.

    === OPERATIONAL DIRECTIVES ===
    1. Context-Grounded Responses: Answer the user's query EXCLUSIVELY using the information provided in the CONTEXT block below. Do not draw on outside knowledge or invent details not present in the context.
    2. Factuality & Zero Hallucination: Never invent CLI flags, tool options, parameters, software vulnerabilities, or CVE identifiers. If the CONTEXT block lacks sufficient detail to answer the query, reply with:
    "Insufficient technical context available in the local knowledge base."
    3. Exact Syntax Preservation: Render all command-line examples, script snippets, tool flags, and configurations in appropriate Markdown code blocks (e.g., `bash`, `python`) preserving exact formatting.
    4. Source Attribution: Explicitly cite the source file or document title (e.g.,) whenever detailing specific technical workflows, command flags, or technical guidance.
    5. Concise & Technical Output: Keep explanations concise, scannable, and directly tailored to technical professionals. Avoid preamble, conversational fluff, or generic disclaimers.
    """

    def __init__(self,
                 rag_client: RAGClient,
                 model_name: str = RETRIEVAL_MODEL,
                 model: Optional[Model] = None,
                 ollama_host: str = OLLAMA_HOST):
        self.rag_client = rag_client
        self.model_name = model_name
        self.model = model or OllamaModel(host=ollama_host)

    def _build_context(self, rag_results: List[Dict[str, Any]]) -> str:
        """
        Build a context string from the RAG results.

        :param rag_results: A list of dictionaries containing the RAG results.
        :return: A string representing the context built from the RAG results.
        """
        if not rag_results:
            return "No relevant information found."

        context_blocks = []
        for idx, item in enumerate(rag_results, 1):
            metadata = item.get("metadata") or {}
            source = metadata.get("source", "Unknown Source")
            title = metadata.get("title", "Untitled")
            content = str(item.get("content", "")).strip()
            if not content:
                continue

            block = (
                f"[Source {idx}: {title} (Path: {source})]\n{content}"
            )
            context_blocks.append(block)
        
        return "\n\n---\n\n".join(context_blocks) or "No relevant information found."

    def _retrieve_information(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve information from the RAG model based on the input query.

        :param query: The input query string.
        :param top_k: The number of top results to return.
        :return: A list of dictionaries containing the retrieved information.
        """
        return self.rag_client.query(query, top_k)

    def run(self, user_prompt: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Run the information retrieval process based on the user's prompt.

        :param user_prompt: The input query string from the user.
        :param top_k: The number of top results to return.
        :return: A structured answer and the context used to produce it.
        """

        if not user_prompt or not user_prompt.strip():
            raise ValueError("user_prompt must not be empty")

        rag_results = self._retrieve_information(user_prompt, top_k)

        context = self._build_context(rag_results)

        user_prompt_with_context = f"CONTEXT:\n{context}\n\nUSER QUESTION:\n{user_prompt}"

        response = self.model.chat(
            model=self.model_name,
            messages=[
                ChatMessage(role="system", content=self.SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_prompt_with_context),
            ],
            options={"temperature": RETRIEVAL_TEMPERATURE}
        )
        answer = response.content

        cited_sources = [
            (item.get("metadata") or {}).get("source", "Unknown Source")
            for item in rag_results
        ]

        return {
            "query": user_prompt,
            "response": answer,
            "raw_context": rag_results,
            "cited_sources": cited_sources
        }
    