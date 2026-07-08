# backend/app/ai/providers/groq_provider.py
# ─────────────────────────────────────────────────────────────────────────────
# Groq AI Provider Implementation
# Wraps LangChain's ChatGroq with our provider interface
# ─────────────────────────────────────────────────────────────────────────────

import os
from typing import Any, Dict, List, Optional
from functools import lru_cache

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

from app.ai.providers.base import BaseAIProvider, BaseEmbeddingProvider, BaseChatProvider


class GroqProvider(BaseAIProvider, BaseChatProvider):
    """Groq AI provider implementation."""
    
    # Available Groq models
    AVAILABLE_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
    ]
    
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key or os.environ.get("GROQ_API_KEY"), **kwargs)
    
    def get_llm(self, model: str = DEFAULT_MODEL, temperature: float = 0.0, 
                max_tokens: int = 1024, **kwargs) -> ChatGroq:
        """Get a Groq LLM instance."""
        return ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
            **kwargs
        )
    
    def get_embeddings(self, model: str = "BAAI/bge-large-en-v1.5", **kwargs) -> HuggingFaceEmbeddings:
        """Get HuggingFace embeddings (Groq doesn't provide embeddings)."""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={"device": device},
            **kwargs
        )
    
    def get_chat_model(self, model: str = DEFAULT_MODEL, **kwargs) -> ChatGroq:
        """Get a Groq chat model instance."""
        return self.get_llm(model=model, **kwargs)
    
    def available_models(self) -> List[str]:
        """Return list of available Groq models."""
        return self.AVAILABLE_MODELS
    
    def validate_api_key(self) -> bool:
        """Validate the Groq API key."""
        if not self.api_key:
            return False
        try:
            # Try to create a simple model instance
            llm = self.get_llm(max_tokens=1)
            return True
        except Exception:
            return False
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from messages."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        llm = self.get_chat_model(**kwargs)
        response = llm.invoke(langchain_messages)
        return response.content
    
    def generate_stream(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a streaming response from messages."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        
        llm = self.get_chat_model(**kwargs)
        for chunk in llm.stream(langchain_messages):
            yield chunk.content

    def transcribe_audio(self, audio_file: bytes, filename: str = "audio.webm", **kwargs) -> str:
        """Transcribe audio using Groq's Whisper model."""
        import requests
        
        model = kwargs.get("model", "whisper-large-v3-turbo")
        language = kwargs.get("language", "en")
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        
        files = {
            "file": (filename, audio_file),
        }
        data = {
            "model": model,
            "response_format": "json",
            "language": language,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            response = requests.post(url, files=files, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("text", "")
        except requests.exceptions.Timeout:
            raise Exception("Transcription request timed out. The audio file may be too large or the service is slow.")
        except requests.exceptions.HTTPError as e:
            error_detail = response.text if response.text else str(e)
            raise Exception(f"Groq API error ({response.status_code}): {error_detail}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Transcription request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during transcription: {str(e)}")


# Singleton instance for backward compatibility
@lru_cache(maxsize=1)
def get_groq_provider() -> GroqProvider:
    """Get cached Groq provider instance."""
    return GroqProvider()
