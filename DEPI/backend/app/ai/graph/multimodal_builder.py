# backend/app/ai/graph/multimodal_builder.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Pipeline Graph Builder
# Builds the real LangGraph that executes an uploaded file end-to-end.
#
#   ENTRY -> route -> {vision | ocr | text | finalize}
#                         |
#                         v
#                    lab? (conditional) -> drug? (conditional) -> finalize -> END
#
# The extraction branch (vision/ocr/text) is chosen by the LLM-driven processor
# decision stored on the ProcessingContext. Lab interpretation and drug
# interaction are conditional enrichments based on document type and extracted
# content. Every path converges on `finalize_node` so the pipeline always
# produces a structured result.
# ─────────────────────────────────────────────────────────────────────────────

from functools import lru_cache

from langgraph.graph import StateGraph, END

from app.ai.graph.multimodal_nodes import (
    drug_node,
    finalize_node,
    lab_node,
    maybe_drug,
    maybe_lab,
    medical_image_node,
    ocr_node,
    route_after_route,
    route_node,
    text_node,
    vision_node,
)
from app.ai.graph.state import MultimodalPipelineState


def build_multimodal_graph():
    """Compile and return the multimodal upload execution graph."""
    workflow = StateGraph(MultimodalPipelineState)

    # Nodes
    workflow.add_node("route", route_node)
    workflow.add_node("vision", vision_node)
    workflow.add_node("ocr", ocr_node)
    workflow.add_node("text", text_node)
    workflow.add_node("medical_image", medical_image_node)
    workflow.add_node("lab", lab_node)
    workflow.add_node("drug", drug_node)
    workflow.add_node("finalize", finalize_node)

    # Entry
    workflow.set_entry_point("route")

    # Conditional extraction branch off `route`
    workflow.add_conditional_edges(
        "route",
        route_after_route,
        {
            "vision": "vision",
            "ocr": "ocr",
            "text": "text",
            "medical_image": "medical_image",
            "finalize": "finalize",
        },
    )

    # Each extraction node flows into the optional lab interpretation step
    for node in ("vision", "ocr", "text", "medical_image"):
        workflow.add_conditional_edges(
            node,
            maybe_lab,
            {"lab": "lab", "drug": "drug"},
        )

    # Lab -> optional drug interaction
    workflow.add_conditional_edges(
        "lab",
        maybe_drug,
        {"drug": "drug", "finalize": "finalize"},
    )

    # Drug -> finalize
    workflow.add_edge("drug", "finalize")

    # Terminate
    workflow.add_edge("finalize", END)

    return workflow.compile()


@lru_cache(maxsize=1)
def get_multimodal_graph():
    """Return a cached compiled multimodal graph instance."""
    return build_multimodal_graph()
