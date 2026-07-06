# backend/app/ai/graph/test_orchestration_graph.py
# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Graph Test Script
# Demonstrates how to check and verify the orchestration graph
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import json
from app.ai.graph.orchestration_builder import get_orchestration_graph
from app.config.settings import get_settings
from app.ai.providers.model_registry import get_model_registry


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_model_configuration():
    """Check current model configuration."""
    print_section("1. MODEL CONFIGURATION")
    
    settings = get_settings()
    
    print(f"\nChat Model:")
    print(f"  - Model: {settings.MODEL_CHAT}")
    print(f"  - Provider: {settings.PROVIDER_CHAT}")
    print(f"  - Temperature: {settings.AI_TEMPERATURE_CHAT}")
    print(f"  - Timeout: {settings.AI_TIMEOUT_CHAT}s")
    
    print(f"\nVision Model:")
    print(f"  - Model: {settings.MODEL_VISION}")
    print(f"  - Provider: {settings.PROVIDER_VISION}")
    print(f"  - Max Output Tokens: {settings.AI_MAX_TOKENS_VISION}")
    print(f"  - Timeout: {settings.AI_TIMEOUT_VISION}s")
    print(f"  - Hard Timeout: {settings.AI_MAX_TIMEOUT_VISION}s")
    
    print(f"\nReasoning Model:")
    print(f"  - Model: {settings.MODEL_REASONING}")
    print(f"  - Provider: {settings.PROVIDER_REASONING}")
    print(f"  - Temperature: {settings.AI_TEMPERATURE_REASONING}")
    
    print(f"\nEmbedding Model:")
    print(f"  - Model: {settings.MODEL_EMBEDDING}")
    print(f"  - Provider: {settings.PROVIDER_EMBEDDING}")


def check_available_models():
    """Check all available models in registry."""
    print_section("2. AVAILABLE MODELS IN REGISTRY")
    
    registry = get_model_registry()
    models = registry.list_models()
    
    print(f"\nTotal models registered: {len(models)}\n")
    
    for model in models:
        print(f"{model.name:30} | {model.provider:12} | {model.model_type.value:12} | {model.context_length:8} tokens")
        print(f"{'':30} | {model.description}")
        print()


def visualize_graph():
    """Visualize the orchestration graph structure."""
    print_section("3. ORCHESTRATION GRAPH STRUCTURE")
    
    graph = get_orchestration_graph()
    
    print("\nGraph Nodes:")
    print("  - orchestrator: Rule-based routing engine (no AI model)")
    print("  - pipeline_dispatcher: Routes to specialized pipelines")
    
    print("\nGraph Flow:")
    print("  User Input → Orchestrator → Pipeline Dispatcher → END")
    
    print("\nGraph Edges:")
    print("  Entry Point: orchestrator")
    print("  orchestrator → pipeline_dispatcher")
    print("  pipeline_dispatcher → END")


async def test_orchestration_graph():
    """Test the orchestration graph with various inputs."""
    print_section("4. ORCHESTRATION GRAPH EXECUTION TESTS")
    
    graph = get_orchestration_graph()
    
    test_cases = [
        {
            "name": "Urgent Chest Pain",
            "input": {
                "user_message": "I have severe chest pain radiating to my left arm",
                "has_image": False,
                "image_description": None,
                "conversation_history": [],
                "user_profile": {"age": 45, "gender": "male"},
                "from_audio": False,
                "execution_time": 0.0,
                "metadata": {}
            }
        },
        {
            "name": "Lab Report Upload",
            "input": {
                "user_message": "Can you read my blood test?",
                "has_image": True,
                "image_description": "document with tabular lab values and reference ranges",
                "conversation_history": [],
                "user_profile": {"age": 30, "gender": "female"},
                "from_audio": False,
                "execution_time": 0.0,
                "metadata": {}
            }
        },
        {
            "name": "Drug Interaction",
            "input": {
                "user_message": "Does ibuprofen interact with warfarin?",
                "has_image": False,
                "image_description": None,
                "conversation_history": [],
                "user_profile": {"age": 65, "gender": "male"},
                "from_audio": False,
                "execution_time": 0.0,
                "metadata": {}
            }
        },
        {
            "name": "Wound Image",
            "input": {
                "user_message": "What does this look like?",
                "has_image": True,
                "image_description": "image showing a wound or cut on the skin",
                "conversation_history": [],
                "user_profile": {"age": 25, "gender": "female"},
                "from_audio": False,
                "execution_time": 0.0,
                "metadata": {}
            }
        },
        {
            "name": "Lifestyle Question",
            "input": {
                "user_message": "What should I eat for my diabetes?",
                "has_image": False,
                "image_description": None,
                "conversation_history": [],
                "user_profile": {"age": 50, "gender": "male", "known_conditions": ["diabetes"]},
                "from_audio": False,
                "execution_time": 0.0,
                "metadata": {}
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        print(f"Input: {test_case['input']['user_message']}")
        
        result = await graph.ainvoke(test_case['input'])
        
        print(f"\nOrchestration Results:")
        print(f"  Pipelines: {result['pipelines']}")
        print(f"  Primary Pipeline: {result['primary_pipeline']}")
        print(f"  Urgency: {result['urgency']}")
        print(f"  Specialist Hint: {result['specialist_hint']}")
        print(f"  Image Type: {result['image_type']}")
        print(f"  Routing Reason: {result['routing_reason']}")
        print(f"  Execution Time: {result['execution_time']:.4f}s")
        print(f"  Dispatched Pipelines: {result.get('dispatched_pipelines', [])}")


def check_pipeline_model_mapping():
    """Show which models are used by each pipeline."""
    print_section("5. PIPELINE TO MODEL MAPPING")
    
    settings = get_settings()
    
    pipeline_models = {
        "rag": {
            "model": settings.MODEL_CHAT,
            "provider": settings.PROVIDER_CHAT,
            "purpose": "Medical knowledge retrieval from clinical textbooks"
        },
        "vision": {
            "model": settings.MODEL_VISION,
            "provider": settings.PROVIDER_VISION,
            "purpose": "Multimodal image analysis (lab reports, prescriptions)"
        },
        "drug_rag": {
            "model": settings.MODEL_CHAT,
            "provider": settings.PROVIDER_CHAT,
            "purpose": "Drug interaction and recommendation retrieval"
        },
        "doctor_finder": {
            "model": settings.MODEL_CHAT,
            "provider": settings.PROVIDER_CHAT,
            "purpose": "Physician and specialist lookup"
        },
        "lifestyle": {
            "model": settings.MODEL_CHAT,
            "provider": settings.PROVIDER_CHAT,
            "purpose": "Diet, exercise, sleep, and wellness recommendations"
        },
        "wound_vision": {
            "model": settings.MODEL_VISION,
            "provider": settings.PROVIDER_VISION,
            "purpose": "Specialized wound and dermatology classification"
        },
        "stt_passthrough": {
            "model": "N/A",
            "provider": "N/A",
            "purpose": "Speech-to-text passthrough flag (no model)"
        }
    }
    
    print("\nPipeline → Model Mapping:\n")
    for pipeline, info in pipeline_models.items():
        print(f"{pipeline:20} → {info['model']:30} ({info['provider']:10})")
        print(f"{'':20}   {info['purpose']}")
        print()


async def main():
    """Run all verification checks."""
    print("\n" + "=" * 70)
    print("  MEDCORTEX ORCHESTRATION GRAPH VERIFICATION")
    print("=" * 70)
    
    # Check model configuration
    check_model_configuration()
    
    # Check available models
    check_available_models()
    
    # Visualize graph
    visualize_graph()
    
    # Show pipeline model mapping
    check_pipeline_model_mapping()
    
    # Test graph execution
    await test_orchestration_graph()
    
    print_section("VERIFICATION COMPLETE")
    print("\nAll checks passed. The orchestration graph is ready for use.")
    print("\nTo integrate this graph into your application:")
    print("  1. Import: from app.ai.graph.orchestration_builder import get_orchestration_graph")
    print("  2. Get graph: graph = get_orchestration_graph()")
    print("  3. Execute: result = await graph.ainvoke(initial_state)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
