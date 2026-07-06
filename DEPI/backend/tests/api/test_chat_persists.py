import pytest
from unittest.mock import patch, MagicMock
from app.ai.multimodal.enums import DocumentType, ModalityType
from app.ai.multimodal.schemas import Diagnosis, Medication, UnifiedMedicalContext
from app.models.conversation import Conversation
from app.models.message import Message


@pytest.fixture
def mock_pipeline():
    with patch("app.api.chat.run_rag") as mock_run_rag, \
         patch("app.api.chat.get_lifestyle_recommendations") as mock_rec, \
         patch("app.api.chat.find_doctors") as mock_doctors:
             
        mock_run_rag.return_value = {
            "answer": "This is a mock RAG answer for flu.",
            "suspected_conditions": ["Influenza"],
            "symptoms": ["fever"],
            "sources": [{"book": "Medical Text A", "section": "Flu chapter"}]
        }
        
        mock_rec.return_value = {
            "foods_to_eat": ["soup"],
            "foods_to_avoid": ["spicy"],
            "drinks_to_have": ["water"],
            "drinks_to_avoid": ["alcohol"],
            "exercises_recommended": ["rest"],
            "exercises_to_avoid": ["running"],
            "rest_recommendation": "8 hours sleep",
            "doctor_specialties": ["General Practitioner"]
        }
        
        mock_doctors.return_value = [
            {
                "name": "Dr. Smith",
                "specialty": "General Practitioner",
                "address": "123 Main St",
                "phone": "555-1234",
                "npi": "1234567890",
                "source": "Mock source"
            }
        ]
        
        yield (mock_run_rag, mock_rec, mock_doctors)


def test_chat_persistence_workflow(client, auth_headers, db_session, test_user, mock_pipeline):
    # 1. POST /chat without conversation_id
    response = client.post(
        "/chat",
        json={"message": "I have a fever"},
        headers=auth_headers,
    )
    print("DEBUG RESPONSE:", response.text)
    assert response.status_code == 200
    res_data = response.json()
    conv_id = res_data["conversation_id"]
    assert conv_id is not None
    
    # Verify in DB that conversation and 2 messages were created
    conv = db_session.query(Conversation).filter(Conversation.id == conv_id).first()
    assert conv is not None
    assert conv.user_id == test_user.id
    
    messages = db_session.query(Message).filter(Message.conversation_id == conv_id).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "I have a fever"
    assert messages[1].role == "assistant"
    assert messages[1].content == "This is a mock RAG answer for flu."

    # 2. POST /chat WITH same conversation_id
    response = client.post(
        "/chat",
        json={"message": "What should I eat?", "conversation_id": conv_id},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["conversation_id"] == conv_id
    
    # Verify messages count is now 4
    messages = db_session.query(Message).filter(Message.conversation_id == conv_id).all()
    assert len(messages) == 4
    assert messages[2].role == "user"
    assert messages[2].content == "What should I eat?"
    assert messages[3].role == "assistant"


def test_chat_prefers_uploaded_document_context(client, auth_headers):
    uploaded_context = UnifiedMedicalContext(
        upload_id="upload-doc-1",
        filename="prescription_scan.jpg",
        mime_type="image/jpeg",
        classification=DocumentType.PRESCRIPTION,
        modality=ModalityType.IMAGE,
    )
    uploaded_context.document_information.title = "Prescription Scan"
    uploaded_context.patient_information.name = "Jane Doe"
    uploaded_context.provider_information.name = "Dr. Lee"
    uploaded_context.provider_information.specialty = "Ophthalmology"
    uploaded_context.medications = [
        Medication(name="Artificial Tears", dosage="1 drop", frequency="twice daily")
    ]
    uploaded_context.diagnoses = [
        Diagnosis(name="Dry eye")
    ]
    uploaded_context.clinical_findings = ["Dry eye symptoms"]
    uploaded_context.recommendations = ["Use lubricating drops"]
    uploaded_context.warnings = ["Check expiration date"]
    uploaded_context.overall_confidence = 0.91

    validator = MagicMock()
    validator.validate.return_value = MagicMock(
        validated_response="Uploaded document summary",
        safety_score=0.95,
        issues=[],
    )

    with patch("app.api.chat.run_rag") as mock_run_rag, \
         patch("app.api.chat.get_lifestyle_recommendations") as mock_rec, \
         patch("app.api.chat.find_doctors") as mock_doctors, \
         patch("app.api.chat.ResponseValidator.create_default", return_value=validator):
        mock_rec.return_value = {
            "foods_to_eat": [],
            "foods_to_avoid": [],
            "drinks_to_have": [],
            "drinks_to_avoid": [],
            "exercises_recommended": [],
            "exercises_to_avoid": [],
            "rest_recommendation": "",
            "doctor_specialties": [],
        }
        mock_doctors.return_value = []

        response = client.post(
            "/chat",
            json={
                "message": "What is that document about?",
                "unified_context": uploaded_context.model_dump(mode="json"),
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Uploaded document summary"
    assert payload["suspected_conditions"] == ["Dry eye"]
    mock_run_rag.assert_not_called()
