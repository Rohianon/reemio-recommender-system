"""Reranking service using Pinecone's hosted reranker."""

import os
import structlog

logger = structlog.get_logger()

_pinecone_client = None


def get_pinecone_client():
    global _pinecone_client
    if _pinecone_client is None:
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            logger.warning("PINECONE_API_KEY not set, reranking unavailable")
            return None
        try:
            from pinecone import Pinecone
            _pinecone_client = Pinecone(api_key=api_key)
            logger.info("Pinecone client initialized for reranking")
        except ImportError:
            logger.warning("pinecone package not installed")
            return None
    return _pinecone_client


class RerankerService:

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_pinecone_client()
        return self._client

    def rerank(
        self, query: str, candidates: list[dict], top_k: int | None = None
    ) -> list[dict]:
        if not candidates:
            return []

        if self.client is None:
            logger.warning("Pinecone client not available, returning original ranking")
            return candidates[:top_k] if top_k else candidates

        documents = [self._create_document_text(c) for c in candidates]

        try:
            result = self.client.inference.rerank(
                model="bge-reranker-v2-m3",
                query=query,
                documents=documents,
                top_n=top_k or len(candidates),
                return_documents=False
            )

            reranked = []
            for item in result.data:
                idx = item.index
                candidate = candidates[idx].copy()
                candidate["rerank_score"] = item.score
                candidate["original_score"] = candidate.get("score", 0.0)
                candidate["score"] = item.score
                reranked.append(candidate)

            return reranked

        except Exception as e:
            logger.error("Error during Pinecone reranking", error=str(e))
            return candidates[:top_k] if top_k else candidates

    def _create_document_text(self, candidate: dict) -> str:
        parts = []

        if name := candidate.get("name"):
            parts.append(name)

        if category := candidate.get("category"):
            parts.append(f"Category: {category}")

        if description := candidate.get("description"):
            if len(description) > 200:
                description = description[:200] + "..."
            parts.append(description)

        return " | ".join(parts)

    def create_query_from_user_context(
        self, user_categories: list[str] | None = None, context: str | None = None
    ) -> str:
        parts = []

        if context:
            parts.append(context)

        if user_categories:
            parts.append(f"Interested in: {', '.join(user_categories[:3])}")

        return " ".join(parts) if parts else "Product recommendations"
