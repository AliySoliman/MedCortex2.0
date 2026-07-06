# Tests for the LLM orchestration brain and the multimodal execution graph.
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.multimodal.decision import OrchestrationDecision, OrchestrationDecisionError
from app.ai.multimodal.enums import DocumentType, ModalityType, ProcessorType
from app.ai.multimodal.llm_brain import GroqOrchestratorBrain
from app.ai.multimodal.orchestrator import MultimodalOrchestrator
from app.ai.multimodal.schemas import ProcessingContext, UnifiedMedicalContext
from app.ai.graph.multimodal_nodes import (
    maybe_drug,
    maybe_lab,
    route_after_route,
)
from app.ai.graph.multimodal_builder import build_multimodal_graph


def _context(processor: ProcessorType = ProcessorType.UNKNOWN,
             doc_type: DocumentType = DocumentType.UNKNOWN) -> ProcessingContext:
    return ProcessingContext(
        upload_id="upload-test",
        filename="file",
        mime_type="application/octet-stream",
        file_bytes=b"bytes",
        processor_type=processor,
        document_type=doc_type,
        unified_context=UnifiedMedicalContext(
            upload_id="upload-test",
            filename="file",
            mime_type="application/octet-stream",
            classification=doc_type,
        ),
    )


# --------------------------------------------------------------------------- #
# Brain
# --------------------------------------------------------------------------- #
def test_brain_parses_llm_json_into_decision():
    raw = '{"modality": "image", "document_type": "X-Ray", "processor": "VISION", "confidence": 0.9, "reasoning": "radiograph"}'
    provider = MagicMock()
    provider.generate.return_value = raw

    with patch("app.ai.multimodal.llm_brain.ProviderFactory.get_provider", return_value=provider):
        brain = GroqOrchestratorBrain()

    decision = asyncio.run(brain.decide(_context()))

    assert decision.modality == ModalityType.IMAGE
    assert decision.document_type == DocumentType.XRAY
    assert decision.processor == ProcessorType.VISION
    assert decision.confidence == pytest.approx(0.9)
    assert decision.reasoning == "radiograph"


def test_brain_tolerates_code_fenced_json():
    raw = '```json\n{"modality": "document", "document_type": "Laboratory Report", "processor": "VISION", "confidence": 0.8}\n```'
    provider = MagicMock()
    provider.generate.return_value = raw

    with patch("app.ai.multimodal.llm_brain.ProviderFactory.get_provider", return_value=provider):
        brain = GroqOrchestratorBrain()

    decision = asyncio.run(brain.decide(_context()))

    assert decision.modality == ModalityType.DOCUMENT
    assert decision.document_type == DocumentType.LAB_REPORT
    assert decision.processor == ProcessorType.VISION


def test_brain_raises_on_unparseable_json():
    provider = MagicMock()
    provider.generate.return_value = "not json at all"

    with patch("app.ai.multimodal.llm_brain.ProviderFactory.get_provider", return_value=provider):
        brain = GroqOrchestratorBrain()

    with pytest.raises(OrchestrationDecisionError):
        asyncio.run(brain.decide(_context()))


def test_brain_raises_on_llm_failure():
    provider = MagicMock()
    provider.generate.side_effect = RuntimeError("boom")

    with patch("app.ai.multimodal.llm_brain.ProviderFactory.get_provider", return_value=provider):
        brain = GroqOrchestratorBrain()

    with pytest.raises(OrchestrationDecisionError):
        asyncio.run(brain.decide(_context()))


def test_brain_raises_on_unknown_enum_value():
    raw = '{"modality": "hologram", "document_type": "Unknown", "processor": "UNKNOWN", "confidence": 0.1}'
    provider = MagicMock()
    provider.generate.return_value = raw

    with patch("app.ai.multimodal.llm_brain.ProviderFactory.get_provider", return_value=provider):
        brain = GroqOrchestratorBrain()

    with pytest.raises(OrchestrationDecisionError):
        asyncio.run(brain.decide(_context()))


# --------------------------------------------------------------------------- #
# Orchestrator fallback
# --------------------------------------------------------------------------- #
def test_orchestrator_falls_back_to_heuristics_when_brain_fails():
    failing_brain = MagicMock()
    failing_brain.decide = AsyncMock(side_effect=OrchestrationDecisionError("no llm"))
    failing_brain.provider_name = "test"
    failing_brain.model_name = "test"

    orchestrator = MultimodalOrchestrator(brain=failing_brain)

    # Use a document MIME so the preprocessor passes bytes through unchanged
    # (no PIL resize) — we are testing the classify/route fallback path here.
    context = asyncio.run(orchestrator.process_upload(
        upload_id="upload-fallback",
        filename="report.pdf",
        mime_type="application/pdf",
        file_bytes=b"pdf-bytes",
    ))

    # Heuristic classifier maps document -> DOCUMENT, router maps DOCUMENT -> VISION.
    assert context.modality == ModalityType.DOCUMENT
    assert context.processor_type == ProcessorType.VISION
    assert context.unified_context.processing_metadata.fallback_used is True


def test_orchestrator_uses_brain_decision_when_available():
    decision = OrchestrationDecision(
        modality=ModalityType.DOCUMENT,
        document_type=DocumentType.LAB_REPORT,
        processor=ProcessorType.VISION,
        confidence=0.88,
        reasoning="lab pdf",
    )
    brain = MagicMock()
    brain.decide = AsyncMock(return_value=decision)
    brain.provider_name = "groq"
    brain.model_name = "llama-3.3-70b-versatile"

    orchestrator = MultimodalOrchestrator(brain=brain)

    context = asyncio.run(orchestrator.process_upload(
        upload_id="upload-brain",
        filename="labs.pdf",
        mime_type="application/pdf",
        file_bytes=b"pdf-bytes",
    ))

    assert context.document_type == DocumentType.LAB_REPORT
    assert context.processor_type == ProcessorType.VISION
    assert context.classification_confidence == pytest.approx(0.88)
    assert context.unified_context.processing_metadata.fallback_used is False
    assert context.unified_context.processing_metadata.model_name == "llama-3.3-70b-versatile"


# --------------------------------------------------------------------------- #
# Graph conditional routing
# --------------------------------------------------------------------------- #
def test_route_after_route_branches_by_processor():
    assert route_after_route({"processor": ProcessorType.VISION}) == "vision"
    assert route_after_route({"processor": ProcessorType.OCR}) == "ocr"
    assert route_after_route({"processor": ProcessorType.TEXT}) == "text"
    assert route_after_route({"processor": ProcessorType.UNKNOWN}) == "finalize"


def test_maybe_lab_runs_only_when_flagged_and_values_present():
    ctx = _context(doc_type=DocumentType.LAB_REPORT)
    assert maybe_lab({"needs_lab_interpretation": True, "context": ctx}) == "drug"

    ctx.unified_context.lab_values = []
    assert maybe_lab({"needs_lab_interpretation": True, "context": ctx}) == "drug"
    assert maybe_lab({"needs_lab_interpretation": False, "context": ctx}) == "drug"


def test_maybe_drug_runs_only_with_enough_medications():
    from app.ai.multimodal.schemas import Medication

    ctx = _context()
    assert maybe_drug({"needs_drug_interaction": True, "context": ctx}) == "finalize"

    ctx.unified_context.medications = [Medication(name="warfarin"), Medication(name="aspirin")]
    assert maybe_drug({"needs_drug_interaction": True, "context": ctx}) == "drug"


def test_graph_routes_vision_through_to_finalize(monkeypatch):
    """Image upload: route -> vision -> (no lab) -> (no drug) -> finalize."""
    processed = {"called": False}

    async def fake_vision_process(self, context):
        processed["called"] = True
        context.unified_context.vision_output = "summary"
        return context

    monkeypatch.setattr("app.ai.graph.multimodal_nodes.VisionService.process", fake_vision_process)

    graph = build_multimodal_graph()
    ctx = _context(processor=ProcessorType.VISION, doc_type=DocumentType.XRAY)

    result = asyncio.run(graph.ainvoke({"context": ctx}))

    assert processed["called"] is True
    assert result["context"].unified_context.vision_output == "summary"
    assert result["metadata"]["completed"] is True


def test_graph_runs_lab_enrichment_for_lab_report(monkeypatch):
    """Lab PDF: route -> vision -> lab -> finalize, with lab interpretation recorded."""
    from app.ai.multimodal.schemas import LabValue

    async def fake_vision_process(self, context):
        context.unified_context.lab_values = [LabValue(name="glucose", value=120, unit="mg/dL")]
        return context

    monkeypatch.setattr("app.ai.graph.multimodal_nodes.VisionService.process", fake_vision_process)

    lab_service = MagicMock()
    lab_service.analyze_lab_report.return_value = {"status": "success", "abnormal_count": 1}
    monkeypatch.setattr(
        "app.ai.graph.multimodal_nodes.LabInterpretationService",
        lambda *a, **kw: lab_service,
    )

    graph = build_multimodal_graph()
    ctx = _context(processor=ProcessorType.VISION, doc_type=DocumentType.LAB_REPORT)

    result = asyncio.run(graph.ainvoke({"context": ctx}))

    lab_service.analyze_lab_report.assert_called_once()
    assert result["metadata"]["lab_interpretation"]["abnormal_count"] == 1


def test_graph_runs_drug_enrichment_for_multiple_meds(monkeypatch):
    """Prescription: route -> vision -> drug -> finalize, with interaction check recorded."""
    from app.ai.multimodal.schemas import Medication

    async def fake_vision_process(self, context):
        context.unified_context.medications = [
            Medication(name="warfarin"),
            Medication(name="aspirin"),
        ]
        return context

    monkeypatch.setattr("app.ai.graph.multimodal_nodes.VisionService.process", fake_vision_process)

    checker = MagicMock()
    checker.check.return_value = []
    monkeypatch.setattr(
        "app.ai.graph.multimodal_nodes.InteractionChecker",
        lambda *a, **kw: checker,
    )

    graph = build_multimodal_graph()
    ctx = _context(processor=ProcessorType.VISION, doc_type=DocumentType.PRESCRIPTION)

    result = asyncio.run(graph.ainvoke({"context": ctx}))

    checker.check.assert_called_once()
    assert result["metadata"]["drug_interactions"] == []


def test_graph_text_branch_runs_parser(monkeypatch):
    """Text upload: route -> text -> finalize."""
    parsed = {"called": False}

    async def fake_parse(self, text, context):
        parsed["called"] = True
        return None

    monkeypatch.setattr("app.ai.graph.multimodal_nodes.SharedMedicalParser.parse", fake_parse)

    graph = build_multimodal_graph()
    ctx = _context(processor=ProcessorType.TEXT, doc_type=DocumentType.UNKNOWN)

    result = asyncio.run(graph.ainvoke({"context": ctx}))

    assert parsed["called"] is True
    assert result["metadata"]["completed"] is True
