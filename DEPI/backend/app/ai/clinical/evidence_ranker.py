# backend/app/ai/clinical/evidence_ranker.py
# ─────────────────────────────────────────────────────────────────────────────
# Evidence Ranker
# Ranks retrieved evidence sources by keyword relevance to a clinical query.
# ─────────────────────────────────────────────────────────────────────────────

import re
from typing import Any, Dict, List
from pydantic import BaseModel


class EvidenceSource(BaseModel):
    source: str
    relevance_score: float
    section: str
    text_snippet: str


class EvidenceRanker:
    """
    Ranks a list of retrieved document sources by their keyword overlap
    with a given clinical query. Fully deterministic — no LLM dependency.
    """

    def rank(self, sources: List[Dict[str, Any]], query: str) -> List[EvidenceSource]:
        """
        Score and sort evidence sources by relevance to query.

        Args:
            sources: List of source dicts from RAG retrieval.
                     Expected keys: 'book' or 'source', 'section', 'text' or 'page_content'.
            query: The clinical query string.

        Returns:
            List of EvidenceSource sorted descending by relevance_score.
        """
        if not sources or not query:
            return []

        query_tokens = set(self._tokenize(query))
        results: List[EvidenceSource] = []

        for src in sources:
            source_name = src.get("book") or src.get("source") or "Unknown Source"
            section = src.get("section") or src.get("docling_headings") or ""
            text = src.get("text") or src.get("page_content") or ""

            combined = f"{source_name} {section} {text}".lower()
            combined_tokens = set(self._tokenize(combined))

            overlap = query_tokens & combined_tokens
            score = len(overlap) / max(len(query_tokens), 1)
            # Boost score if query terms appear in title/section
            title_tokens = set(self._tokenize(f"{source_name} {section}"))
            title_overlap = query_tokens & title_tokens
            score += 0.2 * (len(title_overlap) / max(len(query_tokens), 1))
            score = round(min(score, 1.0), 4)

            results.append(EvidenceSource(
                source=source_name,
                relevance_score=score,
                section=section,
                text_snippet=text[:300],
            ))

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def _tokenize(self, text: str) -> List[str]:
        """Split text into lowercase tokens, stripping punctuation."""
        return [t for t in re.findall(r"[a-z']+", text.lower()) if len(t) > 2]
