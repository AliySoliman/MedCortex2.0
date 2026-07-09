import logging
import os
import time
from typing import Any, Dict

from google import genai
from google.genai import types

from app.config.settings import get_settings


logger = logging.getLogger("medcortex.gemini")


class GeminiVisionProvider:

    def __init__(self, model_name: str):
        settings = get_settings()
        api_key = settings.GEMINI_API_KEY or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key is not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY.")

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        settings = get_settings()
        max_output_tokens = settings.AI_MAX_TOKENS_VISION
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            max_output_tokens=max_output_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=settings.AI_GEMINI_THINKING_BUDGET,
            ),
        )
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_prompt),
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=mime_type,
                    ),
                ],
            )
        ]

        started = time.perf_counter()
        logger.info(
            "Gemini vision request prepared",
            extra={
                "gemini": _request_metrics(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                    image_bytes=image_bytes,
                    mime_type=mime_type,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
            },
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Gemini vision response received",
            extra={"gemini": {"model": self.model_name, "elapsed_ms": elapsed_ms}},
        )

        # response.text can be None when the model returns no text candidates
        # (e.g. safety block or empty response). Return an empty string rather
        # than propagating a None that would crash the caller.
        return response.text or ""


def _request_metrics(
    *,
    model: str,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
    image_bytes: bytes,
    mime_type: str,
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, Any]:
    """Return non-secret Gemini request diagnostics without logging PHI bytes."""
    return {
        "model": model,
        "mime_type": mime_type,
        "image_bytes": len(image_bytes),
        "system_prompt_chars": len(system_prompt or ""),
        "user_prompt_chars": len(user_prompt or ""),
        "contents_type": type(contents).__name__,
        "content_count": len(contents),
        "content_roles": [content.role for content in contents],
        "part_types": [
            [
                "text" if getattr(part, "text", None) is not None else "inline_data"
                for part in content.parts or []
            ]
            for content in contents
        ],
        "config": config.model_dump(exclude_none=True, by_alias=False),
    }
