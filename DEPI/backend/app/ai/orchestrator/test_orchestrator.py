# backend/app/ai/orchestrator/test_orchestrator.py
# ─────────────────────────────────────────────────────────────────────────────
# Test script for MedCortex Orchestration Engine
# ─────────────────────────────────────────────────────────────────────────────

import json
from app.ai.orchestrator import OrchestratorEngine, OrchestratorInput


def test_urgent_chest_pain():
    """Test: User with severe chest pain radiating to left arm."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="I have severe chest pain radiating to my left arm",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 1: Urgent Chest Pain")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_lab_report_upload():
    """Test: User uploads lab report."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="Can you read my blood test?",
        has_image=True,
        image_description="document with tabular lab values and reference ranges"
    )
    output = engine.route(input_data)
    print("Test 2: Lab Report Upload")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_wound_image():
    """Test: User uploads wound image."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="What does this look like?",
        has_image=True,
        image_description="image showing a wound or cut on the skin"
    )
    output = engine.route(input_data)
    print("Test 3: Wound Image")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_drug_interaction():
    """Test: Drug interaction question."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="Does ibuprofen interact with warfarin?",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 4: Drug Interaction")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_lifestyle_question():
    """Test: Lifestyle/diet question."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="What should I eat for my diabetes?",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 5: Lifestyle/Diet Question")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_general_symptoms():
    """Test: General symptoms without image."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="I have a headache and feel nauseous",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 6: General Symptoms")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_audio_input():
    """Test: Audio input with lifestyle question."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="How much exercise should I get each week?",
        has_image=False,
        from_audio=True
    )
    output = engine.route(input_data)
    print("Test 7: Audio Input - Exercise")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_doctor_request():
    """Test: Explicit doctor request."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="I need to find a cardiologist near me",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 8: Doctor Request")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_xray_image():
    """Test: X-ray image upload."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="Can you analyze this x-ray?",
        has_image=True,
        image_description="x-ray image showing chest and ribs"
    )
    output = engine.route(input_data)
    print("Test 9: X-ray Image")
    print(json.dumps(output.model_dump(), indent=2))
    print()


def test_greeting():
    """Test: Greeting/fallback."""
    engine = OrchestratorEngine()
    input_data = OrchestratorInput(
        user_message="Hello, how are you?",
        has_image=False
    )
    output = engine.route(input_data)
    print("Test 10: Greeting/Fallback")
    print(json.dumps(output.model_dump(), indent=2))
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("MedCortex Orchestration Engine Test Suite")
    print("=" * 60)
    print()
    
    test_urgent_chest_pain()
    test_lab_report_upload()
    test_wound_image()
    test_drug_interaction()
    test_lifestyle_question()
    test_general_symptoms()
    test_audio_input()
    test_doctor_request()
    test_xray_image()
    test_greeting()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
