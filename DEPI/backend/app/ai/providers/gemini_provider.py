# backend/app/ai/providers/gemini_provider.py
# ─────────────────────────────────────────────────────────────────────────────
# Gemini AI Provider Implementation
# Wraps Google's Gen AI SDK for multimodal document and image understanding
# ─────────────────────────────────────────────────────────────────────────────

import base64
import binascii
import logging
import os
import time
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.ai.providers.base import BaseAIProvider, BaseChatProvider


logger = logging.getLogger("medcortex.gemini")


class GeminiProvider(BaseAIProvider, BaseChatProvider):
    """Gemini provider implementation for multimodal understanding."""

    AVAILABLE_MODELS = [
        "gemini-3.5-flash",
        "gemini-3.1-flash-lite",
    ]

    DEFAULT_MODEL = "gemini-3.1-flash-lite"

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        super().__init__(resolved_key, **kwargs)
        self._client = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise ValueError("Gemini API key is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY.")
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def get_llm(self, model: str = DEFAULT_MODEL, temperature: float = 0.0, max_tokens: int = 1024, **kwargs) -> Any:
        """Return the provider itself as a lightweight LLM wrapper."""
        self.config.update({"model": model, "temperature": temperature, "max_tokens": max_tokens, **kwargs})
        return self

    def get_embeddings(self, model: str, **kwargs) -> Any:
        raise NotImplementedError("GeminiProvider does not provide embeddings.")

    def get_chat_model(self, model: str, **kwargs) -> Any:
        """Return the provider itself for compatibility with the provider factory."""
        self.config.update({"model": model, **kwargs})
        return self

    def available_models(self) -> List[str]:
        return self.AVAILABLE_MODELS

    def validate_api_key(self) -> bool:
        return bool(self.api_key)

    def generate(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        model = kwargs.pop("model", self.config.get("model", self.DEFAULT_MODEL))
        temperature = kwargs.pop("temperature", self.config.get("temperature", 0.0))
        max_tokens = kwargs.pop("max_tokens", self.config.get("max_tokens", 1024))
        response_schema = kwargs.pop("response_schema", None)
        # Consume (and discard) any extra keys that callers pass but the SDK
        # does not accept — prevents TypeError from strict GenerateContentConfig.
        kwargs.pop("response_mime_type", None)
        # Drain any remaining unknown kwargs silently so we never forward them
        # to the SDK config (which is Pydantic-strict and rejects unknown fields).
        kwargs.clear()

        system_instruction = _extract_system_instruction(messages)
        contents = _build_contents(messages)
        response_mime_type = "application/json" if response_schema else "text/plain"

        # The google-genai SDK requires responseSchema to be a types.Schema
        # object, not a raw dict.  Convert if necessary, but only when a
        # schema was actually provided — passing responseSchema=None with
        # responseMimeType="text/plain" is the correct no-schema path.
        sdk_schema: Optional[types.Schema] = None
        if response_schema is not None:
            if isinstance(response_schema, dict):
                try:
                    sdk_schema = types.Schema(**response_schema)
                except Exception:
                    # Schema conversion failed — fall back to plain text to
                    # avoid crashing the whole parser call.
                    response_mime_type = "text/plain"
                    sdk_schema = None
            else:
                sdk_schema = response_schema  # already a types.Schema

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type=response_mime_type,
            response_schema=sdk_schema,
            system_instruction=system_instruction or None,
        )

        started = time.perf_counter()
        logger.info(
            "Gemini generate request prepared",
            extra={
                "gemini": {
                    "model": model,
                    "content_count": len(contents),
                    "content_shapes": _content_shapes(contents),
                    "system_instruction_chars": len(system_instruction or ""),
                    "config": config.model_dump(exclude_none=True, by_alias=False),
                }
            },
        )
        response = self._get_client().models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Gemini generate response received",
            extra={"gemini": {"model": model, "elapsed_ms": elapsed_ms}},
        )
        return _extract_response_text(response)

    def generate_stream(self, messages: List[Dict[str, Any]], **kwargs):
        model = kwargs.pop("model", self.config.get("model", self.DEFAULT_MODEL))
        temperature = kwargs.pop("temperature", self.config.get("temperature", 0.0))
        max_tokens = kwargs.pop("max_tokens", self.config.get("max_tokens", 1024))
        system_instruction = _extract_system_instruction(messages)
        contents = _build_contents(messages)

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction or None,
            **kwargs,
        )

        for chunk in self._get_client().models.generate_content_stream(
            model=model,
            contents=contents,
            config=config,
        ):
            yield getattr(chunk, "text", "") or ""


def _extract_system_instruction(messages: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for message in messages:
        if message.get("role") == "system":
            content = message.get("content", "")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
    return "\n".join(parts)


def _build_contents(messages: List[Dict[str, Any]]) -> List[types.Content]:
    contents: List[types.Content] = []
    for message in messages:
        role = _to_gemini_role(str(message.get("role", "user")))
        if role == "system":
            continue

        content = message.get("content", "")
        if isinstance(content, str):
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=content)],
                )
            )
            continue

        if isinstance(content, list):
            parts: List[types.Part] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type")
                if item_type == "text" and item.get("text"):
                    parts.append(types.Part.from_text(text=str(item["text"])))
                elif item_type in {"image_url", "image"}:
                    url = ""
                    if isinstance(item.get("image_url"), dict):
                        url = str(item["image_url"].get("url") or "")
                    elif isinstance(item.get("url"), str):
                        url = str(item["url"])
                    part = _part_from_data_url(url)
                    if part is not None:
                        parts.append(part)
            if parts:
                contents.append(types.Content(role=role, parts=parts))
            continue

        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=str(content))],
            )
        )
    return contents


def _part_from_data_url(url: str) -> Optional[types.Part]:
    if not url.startswith("data:") or ";base64," not in url:
        return None
    mime_type, encoded = url.split(";base64,", 1)
    mime_type = mime_type.replace("data:", "")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return None
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def _to_gemini_role(role: str) -> str:
    if role == "system":
        return "system"
    if role in {"assistant", "model"}:
        return "model"
    return "user"


def _content_shapes(contents: List[types.Content]) -> List[Dict[str, Any]]:
    shapes: List[Dict[str, Any]] = []
    for content in contents:
        shapes.append(
            {
                "role": content.role,
                "parts": [
                    "text" if getattr(part, "text", None) is not None else "inline_data"
                    for part in content.parts or []
                ],
            }
        )
    return shapes


def _extract_response_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            part_text = getattr(part, "text", None)
            if isinstance(part_text, str) and part_text.strip():
                return part_text.strip()
    return str(response).strip()
