# backend/app/ai/shared/medical_parser.py
# ─────────────────────────────────────────────────────────────────────────────
# Shared Medical Parser
# Parses unstructured medical text into UnifiedMedicalContext
# ─────────────────────────────────────────────────────────────────────────────

import json
from typing import Any, Dict, List

from app.ai.multimodal.interfaces import BaseMedicalParser
from app.ai.multimodal.schemas import (
    Diagnosis,
    LabValue,
    Medication,
    ProcessingContext,
)
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage
from app.ai.providers.provider_factory import ProviderFactory
from app.config.settings import get_settings


class SharedMedicalParser(BaseMedicalParser):
    """
    Parses raw text (from either OCR or Vision) into the UnifiedMedicalContext
    using a configured LLM provider.
    """
    
    def __init__(self, provider_name: str = None, model_name: str = None):
        settings = get_settings()
        self.provider_name = provider_name or settings.PROVIDER_DOCUMENT
        self.fallback_provider_name = settings.PROVIDER_CHAT
        self.model_name = model_name or settings.MODEL_DOCUMENT
        
    async def parse(self, text: str, context: ProcessingContext) -> None:
        upload_id = context.upload_id
        MultimodalLogger.log_stage_start(PipelineStage.PARSER_STARTED, upload_id)
        
        try:
            # Prepare the prompt
            system_prompt = (
                "You are an expert medical data extractor. "
                "Extract the following information from the provided text into JSON: "
                "patient (dict with name, age, gender, patient_id, dob), "
                "doctor (dict with name, specialty, organization), "
                "document_title (string), report_type (string), test_date (string), "
                "medications (list of dicts with name, dosage, frequency, route), "
                "diagnoses (list of strings), lab_values (list of dicts with test_name, value, unit, reference_range, flag), "
                "notes (list of strings), and recommendations (list of strings). "
                "Also provide a list of 'clinical_findings'. "
                "Ensure your output is strictly valid JSON matching this schema."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Text to parse:\n\n{text}"}
            ]
            
            # Fetch provider and model
            # Note: ProviderFactory usually comes from app.ai.providers
            # Here we mock the parsing logic if provider fails or is unconfigured
            parsed_data = None
            try:
                provider = ProviderFactory.get_provider(self.provider_name)
                response_str = provider.generate(
                    messages,
                    temperature=0.0,
                    model=self.model_name,
                    response_schema=_medical_extraction_schema(),
                )
                parsed_data = _parse_json_response(response_str)
            except Exception as e:
                MultimodalLogger.log_event(
                    PipelineStage.PARSER_STARTED,
                    upload_id,
                    f"Primary semantic parser failed: {e}. Falling back to Groq.",
                )
                try:
                    fallback_provider = ProviderFactory.get_provider(self.fallback_provider_name)
                    response_str = fallback_provider.generate(messages, temperature=0.0)
                    parsed_data = _parse_json_response(response_str)
                except Exception as fallback_exc:
                    MultimodalLogger.log_event(
                        PipelineStage.PARSER_STARTED,
                        upload_id,
                        f"Fallback parser failed: {fallback_exc}. Structured extraction unavailable.",
                    )
                    # Set structured extraction unavailable state instead of mock data
                    parsed_data = {
                        "patient": {},
                        "doctor": {},
                        "medications": [],
                        "diagnoses": [],
                        "lab_values": [],
                        "notes": [],
                        "clinical_findings": ["Structured extraction unavailable - relying on vision output"],
                    }
            
            # Populate unified context IN PLACE
            patient = parsed_data.get("patient", {}) or {}
            provider = parsed_data.get("doctor", {}) or {}
            medications = _coerce_list_of_dicts(parsed_data.get("medications", []))
            diagnoses = _coerce_list_of_strings(parsed_data.get("diagnoses", []))
            lab_values = _coerce_list_of_dicts(parsed_data.get("lab_values", []))
            notes = _coerce_list_of_strings(parsed_data.get("notes", []))
            findings = _coerce_list_of_strings(parsed_data.get("clinical_findings", []))

            context.unified_context.structured_entities = {
                "patient": patient,
                "doctor": provider,
                "medications": medications,
                "diagnoses": diagnoses,
                "lab_values": lab_values,
                "notes": notes,
            }

            context.unified_context.patient_information.name = patient.get("name")
            context.unified_context.patient_information.age = patient.get("age")
            context.unified_context.patient_information.patient_id = patient.get("patient_id")
            context.unified_context.document_information.title = (
                parsed_data.get("document_title")
                or parsed_data.get("report_type")
                or provider.get("name")
            )
            context.unified_context.document_information.date = parsed_data.get("test_date")
            context.unified_context.provider_information.name = provider.get("name")
            context.unified_context.provider_information.specialty = provider.get("specialty")
            context.unified_context.provider_information.organization = provider.get("organization")

            context.unified_context.medications = [_build_medication(item) for item in medications]
            context.unified_context.diagnoses = [_build_diagnosis(item) for item in diagnoses]
            context.unified_context.lab_values = [_build_lab_value(item) for item in lab_values]
            context.unified_context.clinical_findings.extend(findings)
            context.unified_context.recommendations.extend(_coerce_list_of_strings(parsed_data.get("recommendations", [])))
            context.unified_context.parser_confidence = 0.95
            context.unified_context.confidence_scores.parser = 0.95
            context.unified_context.overall_confidence = max(
                context.unified_context.overall_confidence,
                0.95,
            )
            context.unified_context.confidence_scores.overall = context.unified_context.overall_confidence
            
            MultimodalLogger.log_stage_complete(PipelineStage.PARSER_COMPLETED, upload_id)
            
        except Exception as e:
            MultimodalLogger.log_stage_error(PipelineStage.PARSER_COMPLETED, upload_id, str(e))
            raise


def _coerce_list_of_strings(value: Any) -> List[str]:
    if not isinstance(value, list):
        return [str(value)] if value else []
    result: List[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            text = item.get("name") or item.get("text") or item.get("description")
            if text:
                result.append(str(text).strip())
    return result


def _coerce_list_of_dicts(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _build_medication(payload: Dict[str, Any]) -> Medication:
    name = payload.get("name") or payload.get("text") or payload.get("description") or "Unknown"
    return Medication(
        name=name,
        code=payload.get("code"),
        system=payload.get("system"),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
        dosage=payload.get("dosage"),
        frequency=payload.get("frequency"),
        route=payload.get("route"),
        status=payload.get("status") or "active",
    )


def _build_diagnosis(payload: str | Dict[str, Any]) -> Diagnosis:
    if isinstance(payload, str):
        return Diagnosis(name=payload)
    name = payload.get("name") or payload.get("text") or payload.get("description") or "Unknown"
    return Diagnosis(
        name=name,
        code=payload.get("code"),
        system=payload.get("system"),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
        status=payload.get("status") or "active",
        severity=payload.get("severity"),
    )


def _build_lab_value(payload: Dict[str, Any]) -> LabValue:
    name = payload.get("name") or payload.get("test_name") or payload.get("text") or payload.get("description") or "Unknown"
    return LabValue(
        name=name,
        code=payload.get("code"),
        system=payload.get("system"),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
        value=payload.get("value"),
        unit=payload.get("unit"),
        reference_range=payload.get("reference_range"),
        flag=payload.get("flag"),
    )


def _parse_json_response(response_str: str) -> Dict[str, Any]:
    if "```json" in response_str:
        json_str = response_str.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in response_str:
        json_str = response_str.split("```", 1)[1].strip()
    else:
        json_str = response_str.strip()
    return json.loads(json_str)


def _medical_extraction_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "patient": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "string"},
                    "gender": {"type": "string"},
                    "patient_id": {"type": "string"},
                    "dob": {"type": "string"},
                },
            },
            "doctor": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "specialty": {"type": "string"},
                    "organization": {"type": "string"},
                },
            },
            "document_title": {"type": "string"},
            "report_type": {"type": "string"},
            "test_date": {"type": "string"},
            "medications": {"type": "array", "items": {"type": "object"}},
            "diagnoses": {"type": "array", "items": {"type": "string"}},
            "lab_values": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "test_name": {"type": "string"},
                        "text": {"type": "string"},
                        "description": {"type": "string"},
                        "value": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "number"},
                            ]
                        },
                        "unit": {"type": "string"},
                        "reference_range": {"type": "string"},
                        "flag": {"type": "string"},
                    },
                },
            },
            "notes": {"type": "array", "items": {"type": "string"}},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "clinical_findings": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["patient", "doctor", "clinical_findings"],
    }
