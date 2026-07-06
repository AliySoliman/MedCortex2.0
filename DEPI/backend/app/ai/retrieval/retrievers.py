# backend/app/ai/retrieval/retrievers.py
# ─────────────────────────────────────────────────────────────────────────────
# Clinical Retriever
# Handles hybrid search (vector + keyword) over global textbook base and
# longitudinal patient timelines.
# ─────────────────────────────────────────────────────────────────────────────

from functools import lru_cache
from typing import List, Dict, Any, Optional
import json

from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

PINECONE_INDEX   = "medical-assistant"
PINECONE_NS      = "medical_textbooks_base"
EMBEDDING_MODEL  = "BAAI/bge-large-en-v1.5"
RETRIEVER_K      = 5
RETRIEVER_FETCH  = 12

@lru_cache(maxsize=1)
def _get_embeddings() -> HuggingFaceEmbeddings:
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": device},
    )

@lru_cache(maxsize=1)
def _get_vectorstore() -> PineconeVectorStore:
    return PineconeVectorStore(
        index_name=PINECONE_INDEX,
        embedding=_get_embeddings(),
        namespace=PINECONE_NS,
    )


class ClinicalRetriever:
    """
    Retrieves evidence for clinical queries.
    Uses Pinecone for dense vector retrieval.
    """
    
    def __init__(self):
        self.vectorstore = _get_vectorstore()
        self.retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_FETCH},
        )
        
    def retrieve(self, query: str, patient_context: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Retrieve relevant documents based on the query.
        In a full hybrid system, this would combine dense search with BM25.
        """
        # Dense MMR retrieval
        docs = self.retriever.invoke(query)
        
        # If we had a patient timeline stored in Pinecone under a different namespace,
        # we would retrieve it here and append to the docs list.
        # For now, we return the global medical knowledge.
        
        return docs
        
    def format_docs(self, docs: List[Document]) -> str:
        """Format retrieved chunks with their source metadata."""
        chunks = []
        for doc in docs:
            book    = doc.metadata.get("book_title", "Unknown Book")
            heading = doc.metadata.get("docling_headings", "Unknown Section")
            text    = doc.page_content
            chunks.append(f"Source: {book} | Section: {heading}\nText: {text}")
        return "\n\n---\n\n".join(chunks)
