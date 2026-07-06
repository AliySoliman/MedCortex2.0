# backend/app/ai/graph/orchestration_nodes.py
# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Graph Nodes
# Nodes for the Orchestration Engine graph
# ─────────────────────────────────────────────────────────────────────────────

import time
import logging
from typing import Dict, Any

from app.ai.orchestrator import OrchestratorEngine, OrchestratorInput
from app.ai.orchestrator.schemas import UserProfile, ConversationTurn

logger = logging.getLogger(__name__)


async def orchestrator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the Orchestration Engine to determine which pipelines to activate.
    
    This is the entry point node that analyzes user input and routes to 
    specialized AI pipelines (RAG, vision, drug_rag, doctor_finder, lifestyle, etc.)
    
    Reads from state:
      - 'user_message': The user's query
      - 'has_image': Whether an image was uploaded
      - 'image_description': Description of the image (if available)
      - 'conversation_history': Last 5 turns of conversation
      - 'user_profile': Patient profile (age, gender, conditions, allergies)
      - 'from_audio': Whether input came from speech-to-text
      
    Writes to state:
      - 'pipelines': List of pipeline IDs to activate
      - 'primary_pipeline': The most important pipeline for this input
      - 'urgency': Clinical urgency assessment (routine/soon/urgent)
      - 'specialist_hint': Appropriate medical specialist type
      - 'routing_reason': Explanation of routing decision
      - 'requires_doctor_finder': Boolean shortcut for doctor_finder activation
      - 'image_type': Classified image type (if applicable)
      - 'execution_time': Time taken for orchestration
      - 'metadata': Pipeline metadata
    """
    logger.info("Executing orchestrator_node...")
    start_time = time.time()
    
    # Extract input from state
    user_message = state.get("user_message", "")
    has_image = state.get("has_image", False)
    image_description = state.get("image_description")
    conversation_history_data = state.get("conversation_history", [])
    user_profile_data = state.get("user_profile", {})
    from_audio = state.get("from_audio", False)
    
    # Convert conversation history to ConversationTurn objects
    conversation_turns = []
    for turn in conversation_history_data[-5:]:  # Last 5 turns
        conversation_turns.append(
            ConversationTurn(
                user_message=turn.get("user_message", ""),
                has_image=turn.get("has_image", False),
                image_description=turn.get("image_description")
            )
        )
    
    # Convert user profile to UserProfile object
    user_profile = UserProfile(
        age=user_profile_data.get("age"),
        gender=user_profile_data.get("gender"),
        known_conditions=user_profile_data.get("known_conditions", []),
        allergies=user_profile_data.get("allergies", [])
    )
    
    # Create orchestrator input
    orchestrator_input = OrchestratorInput(
        user_message=user_message,
        has_image=has_image,
        image_description=image_description,
        conversation_history=conversation_turns,
        user_profile=user_profile,
        from_audio=from_audio
    )
    
    # Run orchestration engine
    engine = OrchestratorEngine()
    output = engine.route(orchestrator_input)
    
    execution_time = time.time() - start_time
    
    # Prepare metadata
    metadata = {
        "orchestrator_version": "1.0",
        "pipeline_count": len(output.pipelines),
        "primary_pipeline": output.primary_pipeline,
        "urgency_level": output.urgency,
    }
    
    logger.info(f"Orchestration completed: {output.pipelines} (urgency: {output.urgency})")
    
    return {
        "pipelines": output.pipelines,
        "primary_pipeline": output.primary_pipeline,
        "urgency": output.urgency,
        "specialist_hint": output.specialist_hint,
        "routing_reason": output.routing_reason,
        "requires_doctor_finder": output.requires_doctor_finder,
        "image_type": output.image_type,
        "execution_time": execution_time,
        "metadata": metadata,
    }


async def pipeline_dispatcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatches to the appropriate pipeline nodes based on orchestration decision.
    
    This node acts as a conditional router that executes the selected pipelines
    in the correct order based on the orchestration engine's decision.
    
    Reads from state:
      - 'pipelines': List of pipeline IDs to activate
      - 'primary_pipeline': The primary pipeline
      - 'user_message': The user's query
      - 'has_image': Whether an image was uploaded
      - 'image_description': Description of the image
      
    Writes to state:
      - Pipeline-specific outputs (rag_answer, vision_output, drug_info, etc.)
      - 'dispatched_pipelines': List of pipelines that were dispatched
      - 'metadata': Updated with dispatch information
    """
    logger.info("Executing pipeline_dispatcher_node...")
    
    pipelines = state.get("pipelines", [])
    primary_pipeline = state.get("primary_pipeline")
    
    dispatched_pipelines = []
    pipeline_results = {}
    
    # Dispatch to each pipeline based on orchestration decision
    # This is a placeholder - actual pipeline execution would happen here
    for pipeline in pipelines:
        logger.info(f"Dispatching to pipeline: {pipeline}")
        dispatched_pipelines.append(pipeline)
        
        # Placeholder for actual pipeline execution
        # In production, this would call the actual pipeline nodes
        if pipeline == "rag":
            pipeline_results["rag_answer"] = "RAG response placeholder"
        elif pipeline == "vision":
            pipeline_results["vision_output"] = "Vision analysis placeholder"
        elif pipeline == "drug_rag":
            pipeline_results["drug_info"] = "Drug interaction placeholder"
        elif pipeline == "doctor_finder":
            pipeline_results["doctor_results"] = "Doctor finder placeholder"
        elif pipeline == "lifestyle":
            pipeline_results["lifestyle_recommendations"] = "Lifestyle placeholder"
        elif pipeline == "wound_vision":
            pipeline_results["wound_analysis"] = "Wound analysis placeholder"
        elif pipeline == "stt_passthrough":
            pipeline_results["stt_flag"] = True
    
    metadata = state.get("metadata", {})
    metadata["dispatched_pipelines"] = dispatched_pipelines
    metadata["pipeline_results"] = list(pipeline_results.keys())
    
    return {
        **pipeline_results,
        "dispatched_pipelines": dispatched_pipelines,
        "metadata": metadata,
    }
