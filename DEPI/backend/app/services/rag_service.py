"""Optional mock RAG payload for tests or offline demos (not used by /chat)."""


def get_mock_rag_response() -> dict[str, object]:
    return {
        "answer": "This is a mock RAG answer.",
        "suspected_conditions": ["Upper respiratory infection"],
        "symptoms": ["cough", "fatigue"],
        "sources": [{"book": "Mock textbook", "section": "Chapter 1"}],
    }
