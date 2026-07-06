# backend/app/ai/graph/nodes.py
# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Nodes
# Contains nodes for the Medical AI workflow graph.
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, Any
import logging

from app.ai.agents.coordinator import MedicalCoordinatorAgent
from app.ai.safety.response_validator import ResponseValidator

logger = logging.getLogger(__name__)


async def medical_coordinator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the Agent Layer pipeline.
    
    Reads from state:
      - 'user_message': The user's query
      - 'user_id': (Optional) User ID
      - 'unified_context': (Optional) Parsed context
      - 'conversation_history': (Optional) Chat history
      
    Writes to state:
      - 'rag_answer': The raw generated report
      - 'symptoms': Extracted symptoms
      - 'lifestyle_recommendations': Extracted recommendations
      - 'metadata': Pipeline metadata
    """
    logger.info("Executing medical_coordinator_node...")
    coordinator = MedicalCoordinatorAgent()
    
    query = state.get("user_message", "")
    user_id = state.get("user_id")
    unified_context = state.get("unified_context")
    conversation_history = state.get("conversation_history", [])
    
    # Run the coordinator pipeline
    agent_context = await coordinator.coordinate(
        query=query,
        user_id=user_id,
        unified_context=unified_context,
        conversation_history=conversation_history
    )
    
    # Extract results into state
    report = agent_context.generated_report or "I'm sorry, I was unable to generate a response."

    return {
        "rag_answer": report,
        "symptoms": agent_context.extracted_symptoms,
        "lifestyle_recommendations": {"recommendations": agent_context.recommendations},
        "metadata": {"session_id": agent_context.session_id, "trace": agent_context.agent_trace}
    }


async def safety_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the generated response using the AI Safety Layer.
    
    Reads from state:
      - 'rag_answer': The raw generated report
      - 'user_message': The user's query
      
    Writes to state:
      - 'rag_answer': The safety-validated (and potentially modified) report
      - 'confidence': Safety score
      - 'metadata': Appended with safety metadata
    """
    logger.info("Executing safety_node...")
    response = state.get("rag_answer", "")
    query = state.get("user_message", "")
    
    if not response:
        return state
        
    validator = ResponseValidator.create_default()
    
    # Extract source context text for hallucination checks
    source_context = ""
    # In a real scenario, we'd grab context from state.retrieved_context
    # For now, we pass empty string since retrieval agent puts it in agent_context, not directly in graph state yet.
    
    result = validator.validate(
        response=response,
        query=query,
        source_context=source_context
    )
    
    metadata = state.get("metadata", {})
    metadata["safety"] = result.metadata
    metadata["safety_issues"] = result.issues
    metadata["is_safe"] = result.is_valid
    
    return {
        "rag_answer": result.validated_response,
        "confidence": result.safety_score,
        "metadata": metadata
    }
