import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image
from io import BytesIO

from app.ai.multimodal.enums import ProcessorType
from app.ai.multimodal.schemas import (
    ProcessingContext,
    UnifiedMedicalContext,
)
from app.ai.multimodal.preprocessing import DefaultPreprocessor
from app.ai.shared.medical_parser import SharedMedicalParser
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.provider_factory import ProviderFactory
from app.ai.clinical.lab_interpreter import StandardLabInterpreter, resolve_reference_range
from app.ai.vision.provider import VisionProvider


def _make_processing_context(upload_id: str, filename: str, mime_type: str, processor_type: ProcessorType) -> ProcessingContext:
    return ProcessingContext(
        upload_id=upload_id,
        filename=filename,
        mime_type=mime_type,
        file_bytes=b"fake-bytes",
        processor_type=processor_type,
        unified_context=UnifiedMedicalContext(
            upload_id=upload_id,
            filename=filename,
            mime_type=mime_type,
        ),
    )


def test_upload_routes_image_to_vision(client):
    context = _make_processing_context(
        upload_id="upload-vision",
        filename="scan.jpg",
        mime_type="image/jpeg",
        processor_type=ProcessorType.VISION,
    )

    async def fake_process_upload(*args, **kwargs):
        return context

    async def fake_graph_ainvoke(initial_state):
        pipeline_context = initial_state["context"]
        pipeline_context.unified_context.vision_output = "Vision summary"
        pipeline_context.unified_context.vision_confidence = 0.92
        pipeline_context.unified_context.overall_confidence = 0.92
        return {"context": pipeline_context}

    with patch("app.api.upload.multimodal_engine.process_upload", new=AsyncMock(side_effect=fake_process_upload)), \
         patch("app.api.upload.multimodal_graph.ainvoke", new=AsyncMock(side_effect=fake_graph_ainvoke)):
        response = client.post(
            "/upload",
            files={"file": ("scan.jpg", b"fake-image", "image/jpeg")},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["unified_context"]["vision_output"] == "Vision summary"


def test_upload_routes_pdf_to_vision(client):
    """PDFs route to Vision (Gemini) via the multimodal graph for richer clinical interpretation."""
    context = _make_processing_context(
        upload_id="upload-vision-pdf",
        filename="report.pdf",
        mime_type="application/pdf",
        processor_type=ProcessorType.VISION,
    )

    async def fake_process_upload(*args, **kwargs):
        return context

    async def fake_graph_ainvoke(initial_state):
        pipeline_context = initial_state["context"]
        pipeline_context.unified_context.vision_output = "Doctor's review of lab report"
        pipeline_context.unified_context.vision_confidence = 0.92
        pipeline_context.unified_context.overall_confidence = 0.92
        return {"context": pipeline_context}

    with patch("app.api.upload.multimodal_engine.process_upload", new=AsyncMock(side_effect=fake_process_upload)), \
         patch("app.api.upload.multimodal_graph.ainvoke", new=AsyncMock(side_effect=fake_graph_ainvoke)):
        response = client.post(
            "/upload",
            files={"file": ("report.pdf", b"fake-pdf", "application/pdf")},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["unified_context"]["vision_output"] == "Doctor's review of lab report"


def test_shared_medical_parser_structures_unstructured_text():
    dummy_provider = MagicMock()
    dummy_provider.generate.return_value = (
        '{"patient":{"name":"Jane Doe","patient_id":"123"},"doctor":{"name":"Dr. Lee","specialty":"Ophthalmology","organization":"City Eye"},"medications":[{"name":"Artificial Tears","dosage":"1 drop"}],"diagnoses":["Dry eye"],"lab_values":[{"name":"CRP","value":"5","unit":"mg/L"}],"clinical_findings":["Dry eye symptoms"],"recommendations":["Use lubricating drops"]}'
    )

    with patch("app.ai.shared.medical_parser.ProviderFactory.get_provider", return_value=dummy_provider):
        parser = SharedMedicalParser(provider_name="groq")
        context = _make_processing_context(
            upload_id="upload-parser",
            filename="report.txt",
            mime_type="text/plain",
            processor_type=ProcessorType.UNKNOWN,
        )

        asyncio.run(parser.parse("Clinical note text", context))

    assert context.unified_context.patient_information.name == "Jane Doe"
    assert context.unified_context.provider_information.name == "Dr. Lee"
    assert context.unified_context.medications[0].name == "Artificial Tears"
    assert context.unified_context.diagnoses[0].name == "Dry eye"
    assert context.unified_context.lab_values[0].name == "CRP"
    assert "Dry eye symptoms" in context.unified_context.clinical_findings
    assert "Use lubricating drops" in context.unified_context.recommendations


def test_shared_medical_parser_defaults_to_gemini():
    parser = SharedMedicalParser()
    assert parser.provider_name == "gemini"
    assert parser.model_name == "gemini-2.5-flash"


def test_provider_factory_registers_gemini():
    provider = ProviderFactory.get_provider("gemini")
    assert isinstance(provider, GeminiProvider)


def test_vision_provider_uses_provider_factory_alias():
    dummy_provider = MagicMock()
    dummy_provider.generate.return_value = "Vision read: prescription image with clear text"

    with patch("app.ai.vision.provider.ProviderFactory.get_provider", return_value=dummy_provider):
        provider = VisionProvider(provider_name="groq", model_name="test-vision-model")
        result = asyncio.run(provider.analyze_image(b"image-bytes", "image/png", "upload-123"))

    assert result["raw_text"] == "Vision read: prescription image with clear text"
    assert result["model_used"] == "test-vision-model"


def test_vision_provider_falls_back_when_model_is_decommissioned():
    dummy_provider = MagicMock()

    def generate(messages, **kwargs):
        model = kwargs.get("model", "")
        if model == "gemini-2.5-pro":
            raise RuntimeError("model_decommissioned")
        return "Fallback vision summary"

    dummy_provider.generate.side_effect = generate

    with patch("app.ai.vision.provider.ProviderFactory.get_provider", return_value=dummy_provider):
        provider = VisionProvider(provider_name="gemini", model_name="gemini-2.5-pro")
        result = asyncio.run(provider.analyze_image(b"image-bytes", "image/png", "upload-456"))

    assert result["raw_text"] == "Fallback vision summary"
    assert result["model_used"] == "gemini-2.5-flash"


def test_vision_provider_falls_back_when_model_is_not_found():
    dummy_provider = MagicMock()

    def generate(messages, **kwargs):
        model = kwargs.get("model", "")
        if model == "gemini-2.5-pro":
            raise RuntimeError("model_not_found")
        return "Fallback vision summary"

    dummy_provider.generate.side_effect = generate

    with patch("app.ai.vision.provider.ProviderFactory.get_provider", return_value=dummy_provider):
        provider = VisionProvider(provider_name="gemini", model_name="gemini-2.5-pro")
        result = asyncio.run(provider.analyze_image(b"image-bytes", "image/png", "upload-789"))

    assert result["raw_text"] == "Fallback vision summary"
    assert result["model_used"] == "gemini-2.5-flash"


def test_preprocessor_resizes_oversized_images():
    image = Image.new("RGB", (7000, 4800), color="white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=95)
    oversized_bytes = buffer.getvalue()

    context = _make_processing_context(
        upload_id="upload-large-image",
        filename="large_scan.jpg",
        mime_type="image/jpeg",
        processor_type=ProcessorType.VISION,
    )
    context.file_bytes = oversized_bytes

    preprocessor = DefaultPreprocessor()
    processed_bytes = asyncio.run(preprocessor.preprocess(context))

    assert len(processed_bytes) < len(oversized_bytes)

    processed_image = Image.open(BytesIO(processed_bytes))
    assert processed_image.width * processed_image.height <= 30_000_000


def test_lab_interpreter_recognizes_common_lipid_aliases():
    canonical_name, reference = resolve_reference_range("HDL CHOL")
    assert canonical_name == "hdl cholesterol"
    assert reference is not None

    interpreter = StandardLabInterpreter()
    results = interpreter.interpret_results(
        {
            "TOTAL CHOLESTEROL": 138,
            "TRIGLYCERIDES": 58,
            "HDL CHOL": 43,
            "LDL CHOL": 83,
            "VLDL CHOL": 12,
            "RISK RATIO": 3.21,
        }
    )

    flags = {result.name: result.flag for result in results}
    assert flags["TOTAL CHOLESTEROL"] == "NORMAL"
    assert flags["TRIGLYCERIDES"] == "NORMAL"
    assert flags["HDL CHOL"] == "NORMAL"
    assert flags["LDL CHOL"] == "NORMAL"
    assert flags["VLDL CHOL"] == "NORMAL"
    assert flags["RISK RATIO"] == "NORMAL"
