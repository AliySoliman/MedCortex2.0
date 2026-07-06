# backend/app/ai/multimodal/llm_brain.py
# ─────────────────────────────────────────────────────────────────────────────
# LLM Orchestration Brain
# LLM-driven classify + route for the multimodal orchestrator.
#
# Default brain uses Groq's Llama 3.3 70B (the same model used for RAG
# generation), but the class is fully provider/model agnostic: any provider
# exposing the BaseChatProvider.generate() contract and any model can be
# configured by changing the constructor arguments.
# ─────────────────────────────────────────────────────────────────────────────

import json
import logging
from typing import Any, Dict, List, Optional

from app.ai.multimodal.decision import OrchestrationDecision, OrchestrationDecisionError
from app.ai.multimodal.enums import DocumentType, ModalityType, ProcessorType
from app.ai.multimodal.interfaces import BaseOrchestratorBrain
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.multimodal.utils import get_mime_modality
from app.ai.providers.provider_factory import ProviderFactory

logger = logging.getLogger("medcortex.multimodal.brain")

# Default model — matches the RAG generator (ClinicalGenerator).
DEFAULT_PROVIDER = "groq"
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 512


class GroqOrchestratorBrain(BaseOrchestratorBrain):
    """
    LLM-driven orchestration brain.

    Sends a text-only prompt (filename, MIME type, and a modality hint derived
    from the MIME type) to an LLM and asks it to return a strict-JSON
    `OrchestrationDecision`. The model never receives the raw file bytes, which
    keeps the call cheap and provider-agnostic (works for any text/chat model).

    Provider and model are constructor arguments so any future model of any
    kind can be wired in without touching this class:

        brain = GroqOrchestratorBrain(provider_name="gemini", model_name="gemini-2.5-flash")
    """

    def __init__(
        self,
        provider_name: str = DEFAULT_PROVIDER,
        model_name: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        self.provider_name = provider_name
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._provider = ProviderFactory.get_provider(provider_name)

    async def decide(self, context: ProcessingContext) -> OrchestrationDecision:
        """Ask the LLM to classify and route the upload in one shot."""
        messages = self._build_messages(context)
        raw = self._generate(messages)

        payload = self._parse_json(raw, context.upload_id)
        decision = self._coerce_decision(payload, context.upload_id)

        logger.info(
            "LLM brain decision for %s: modality=%s doc_type=%s processor=%s conf=%.2f",
            context.upload_id,
            decision.modality.value,
            decision.document_type.value,
            decision.processor.value,
            decision.confidence,
        )
        return decision

    # ------------------------------------------------------------------ #
    # Prompt construction
    # ------------------------------------------------------------------ #
    def _build_messages(self, context: ProcessingContext) -> List[Dict[str, Any]]:
        mime_modality = get_mime_modality(context.mime_type)
        allowed_modalities = ", ".join(m.value for m in ModalityType if m != ModalityType.UNKNOWN)
        allowed_doc_types = ", ".join(d.value for d in DocumentType if d != DocumentType.UNKNOWN)
        allowed_processors = ", ".join(p.value for p in ProcessorType if p != ProcessorType.UNKNOWN)

        system_prompt = (
            "You are the multimodal orchestration brain of MedCortex, a clinical AI system. "
            "Given metadata about an uploaded medical file, decide:\n"
            "1. its high-level modality,\n"
            "2. its specific document type,\n"
            "3. which processor should extract its clinical content, and\n"
            "4. a confidence score between 0.0 and 1.0.\n"
            "\n"
            "Processor routing guidance:\n"
            "- VISION: images (skin, wounds, x-ray, MRI, CT, ultrasound, eye) and PDFs/documents "
            "(lab reports, prescriptions, referrals, discharge summaries) — Gemini ingests these "
            "natively and produces richer clinical interpretation than raw OCR.\n"
            "- OCR: only when the file is a scanned document that genuinely needs text extraction.\n"
            "- TEXT: plain-text uploads that need no image/document understanding.\n"
            "\n"
            f"modality must be one of: {allowed_modalities}.\n"
            f"document_type must be one of: {allowed_doc_types}.\n"
            f"processor must be one of: {allowed_processors}.\n"
            "\n"
            "Respond with ONLY a single JSON object, no markdown, no explanation, matching exactly:\n"
            '{"modality": "<one of the modality values>", '
            '"document_type": "<one of the document_type values>", '
            '"processor": "<one of the processor values>", '
            '"confidence": <float 0.0-1.0>, '
            '"reasoning": "<short rationale>"}'
        )

        user_prompt = (
            f"filename: {context.filename}\n"
            f"mime_type: {context.mime_type}\n"
            f"mime_based_modality_hint: {mime_modality}\n"
            "Decide the modality, document_type, processor, confidence, and reasoning."
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    # ------------------------------------------------------------------ #
    # LLM call
    # ------------------------------------------------------------------ #
    def _generate(self, messages: List[Dict[str, Any]]) -> str:
        try:
            return self._provider.generate(
                messages,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except Exception as exc:
            raise OrchestrationDecisionError(
                f"LLM brain call failed ({self.provider_name}/{self.model_name}): {exc}"
            ) from exc

    # ------------------------------------------------------------------ #
    # Parsing / coercion
    # ------------------------------------------------------------------ #
    def _parse_json(self, raw: str, upload_id: str) -> Dict[str, Any]:
        if not raw or not raw.strip():
            raise OrchestrationDecisionError(f"Empty LLM response for {upload_id}.")

        text = raw.strip()
        # Tolerate models that wrap JSON in code fences or prose.
        if text.startswith("```"):
            text = text.strip("`")
            # Drop an optional leading language tag like 'json'.
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        # If there is still surrounding prose, isolate the outermost JSON object.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise OrchestrationDecisionError(
                f"Unparseable LLM JSON for {upload_id}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise OrchestrationDecisionError(f"LLM JSON is not an object for {upload_id}.")
        return payload

    def _coerce_decision(self, payload: Dict[str, Any], upload_id: str) -> OrchestrationDecision:
        try:
            modality = ModalityType(str(payload.get("modality", "unknown")).strip().lower())
        except ValueError:
            raise OrchestrationDecisionError(
                f"Unknown modality '{payload.get('modality')}' for {upload_id}."
            )

        try:
            document_type = DocumentType(str(payload.get("document_type", "Unknown")).strip())
        except ValueError:
            raise OrchestrationDecisionError(
                f"Unknown document_type '{payload.get('document_type')}' for {upload_id}."
            )

        try:
            processor = ProcessorType(str(payload.get("processor", "UNKNOWN")).strip().upper())
        except ValueError:
            raise OrchestrationDecisionError(
                f"Unknown processor '{payload.get('processor')}' for {upload_id}."
            )

        confidence_raw = payload.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        return OrchestrationDecision(
            modality=modality,
            document_type=document_type,
            processor=processor,
            confidence=confidence,
            reasoning=str(payload.get("reasoning") or "") or None,
        )
