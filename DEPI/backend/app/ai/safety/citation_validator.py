"""
citation_validator.py
=====================
Citation validation for the MedCortex AI Safety subsystem.

Validates that citations mentioned in an AI response are traceable to
the retrieved source documents, and extracts citation-like patterns from
free-form response text.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CitationValidation(BaseModel):
    """Validation result for a single citation.

    Attributes:
        citation: The raw citation string as it appeared in the response.
        is_valid: ``True`` if the citation was matched against a source document.
        reason: Human-readable explanation of the validation outcome.
    """

    citation: str
    is_valid: bool
    reason: str


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

#: Numbered inline citations: [1], [2], [1,2], [1-3]
_NUMBERED_CITATION_RE = re.compile(r"\[\s*\d+(?:[,\-]\s*\d+)*\s*\]")

#: Author-year citations: (Smith, 2021) / (Smith et al., 2021)
_AUTHOR_YEAR_RE = re.compile(
    r"\(\s*[A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?,\s*(?:19|20)\d{2}\s*\)"
)

#: Quoted title references: "Study Title Here"
_QUOTED_TITLE_RE = re.compile(r'"([^"]{5,120})"')

#: DOI patterns: doi:10.xxxx/... or https://doi.org/10.xxxx/...
_DOI_RE = re.compile(
    r"(?:doi:\s*|https?://doi\.org/)10\.\d{4,}/[^\s,;)>\"']+",
    re.IGNORECASE,
)

#: URL patterns (general)
_URL_RE = re.compile(r"https?://[^\s,;)>\"']{10,}")

#: Source metadata fields tried in order for title lookup.
_TITLE_FIELDS = ("title", "Title", "source_title", "document_title", "name")


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class CitationValidator:
    """Validate AI-response citations against retrieved source documents.

    A citation is considered **valid** when its source title (extracted from the
    citation string or matched as a quoted title) appears – case-insensitively –
    in the ``title``-like metadata fields of at least one source document.

    Numbered citations (``[1]``, ``[2]``, …) are mapped to source documents by
    their 1-based index in *source_docs*.

    Usage::

        validator = CitationValidator()
        citations = validator.extract_citations(response_text)
        results = validator.validate(citations, source_docs)
        invalid = [r for r in results if not r.is_valid]
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        citations: List[str],
        source_docs: List[Dict],
    ) -> List[CitationValidation]:
        """Validate each citation against the provided source documents.

        Args:
            citations: List of citation strings to validate (typically from
                :meth:`extract_citations`).
            source_docs: List of source document dicts, each expected to
                contain at least a ``title`` (or similar) metadata key.

        Returns:
            A :class:`CitationValidation` for every entry in *citations*.
        """
        results: List[CitationValidation] = []
        source_titles = self._collect_titles(source_docs)

        for citation in citations:
            validation = self._validate_single(citation, source_docs, source_titles)
            results.append(validation)

        return results

    def extract_citations(self, response_text: str) -> List[str]:
        """Extract citation-like patterns from a free-form response.

        Recognises the following forms:

        * Numbered inline: ``[1]``, ``[2,3]``, ``[1-5]``
        * Author-year:     ``(Smith, 2021)``, ``(Jones et al., 2019)``
        * Quoted titles:   ``"Some Article Title"``
        * DOIs:            ``doi:10.1000/xyz123``
        * URLs:            ``https://pubmed.ncbi.nlm.nih.gov/...``

        Args:
            response_text: The raw text of the AI response.

        Returns:
            A deduplicated list of citation strings in order of appearance.
        """
        found: List[str] = []

        for pattern in (
            _NUMBERED_CITATION_RE,
            _AUTHOR_YEAR_RE,
            _DOI_RE,
            _URL_RE,
        ):
            found.extend(m.group(0) for m in pattern.finditer(response_text))

        # Quoted titles – return the full match including quotes.
        for m in _QUOTED_TITLE_RE.finditer(response_text):
            found.append(m.group(0))

        # Deduplicate while preserving order.
        seen: set = set()
        unique: List[str] = []
        for item in found:
            key = item.strip().lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _validate_single(
        self,
        citation: str,
        source_docs: List[Dict],
        source_titles: List[str],
    ) -> CitationValidation:
        """Determine whether a single *citation* is grounded in *source_docs*."""

        # --- Numbered citation: map by index ---
        numbered_match = _NUMBERED_CITATION_RE.fullmatch(citation.strip())
        if numbered_match:
            indices = re.findall(r"\d+", citation)
            valid_indices = [
                i for i in (int(n) - 1 for n in indices)
                if 0 <= i < len(source_docs)
            ]
            if valid_indices:
                titles = [
                    self._get_title(source_docs[i]) or f"Document {i + 1}"
                    for i in valid_indices
                ]
                return CitationValidation(
                    citation=citation,
                    is_valid=True,
                    reason=f"Matched source document(s): {', '.join(titles)}.",
                )
            return CitationValidation(
                citation=citation,
                is_valid=False,
                reason=f"Index {citation} is out of range for the {len(source_docs)} available source(s).",
            )

        # --- Quoted title: substring match ---
        quoted_match = _QUOTED_TITLE_RE.fullmatch(citation.strip())
        if quoted_match:
            inner = quoted_match.group(1).lower()
            matched = next(
                (t for t in source_titles if inner in t or t in inner),
                None,
            )
            if matched:
                return CitationValidation(
                    citation=citation,
                    is_valid=True,
                    reason=f"Title matched source: '{matched[:80]}'.",
                )
            return CitationValidation(
                citation=citation,
                is_valid=False,
                reason=f"Quoted title '{citation[:80]}' not found in source documents.",
            )

        # --- DOI / URL: accept if the raw string appears in any source metadata ---
        citation_lower = citation.lower()
        for doc in source_docs:
            doc_text = " ".join(str(v) for v in doc.values()).lower()
            if citation_lower in doc_text:
                return CitationValidation(
                    citation=citation,
                    is_valid=True,
                    reason="Citation URL/DOI found in source document metadata.",
                )

        # --- Author-year / fallback: fuzzy title search ---
        for title in source_titles:
            words = re.findall(r"[a-z]{4,}", citation_lower)
            if words and any(w in title for w in words):
                return CitationValidation(
                    citation=citation,
                    is_valid=True,
                    reason=f"Partial match with source title: '{title[:80]}'.",
                )

        return CitationValidation(
            citation=citation,
            is_valid=False,
            reason="Citation could not be traced to any retrieved source document.",
        )

    @staticmethod
    def _collect_titles(source_docs: List[Dict]) -> List[str]:
        """Return a list of lowercase title strings from *source_docs*."""
        titles: List[str] = []
        for doc in source_docs:
            title = CitationValidator._get_title(doc)
            if title:
                titles.append(title.lower())
        return titles

    @staticmethod
    def _get_title(doc: Dict) -> Optional[str]:
        """Extract the title value from a document dict using known field names."""
        for field in _TITLE_FIELDS:
            if field in doc:
                return str(doc[field])
        # Check nested 'metadata' sub-dict (common in LangChain Document objects).
        meta = doc.get("metadata") or {}
        if isinstance(meta, dict):
            for field in _TITLE_FIELDS:
                if field in meta:
                    return str(meta[field])
        return None
