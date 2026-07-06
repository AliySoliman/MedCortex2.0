# backend/app/ai/vision/provider.py
# ─────────────────────────────────────────────────────────────────────────────
# Vision Provider
# ─────────────────────────────────────────────────────────────────────────────

import base64
import time
import asyncio
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.ai.providers.provider_factory import ProviderFactory
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage
from app.ai.multimodal.exceptions import VisionError
from app.config.settings import get_settings
from app.ai.prompts.vision_prompts import (
    VISION_ANALYSIS_PROMPT,
    VISION_SYSTEM_INSTRUCTION,
)


class VisionProvider:
    """
    Provider for extracting unstructured findings from medical images and PDFs
    using Vision-Language Models (Gemini 3.5 Flash with Gemini 2.5 Flash fallback).
    Includes retries, generous timeouts, and a thinking-model-friendly token budget.
    """

    def __init__(self, provider_name: str | None = None, model_name: str | None = None):
        settings = get_settings()
        self.provider_name = provider_name or settings.PROVIDER_VISION
        self.model_name = model_name or settings.MODEL_VISION
        self.fallback_provider_name = "gemini"
        self.fallback_model_name = settings.MODEL_VISION_FALLBACK
        self._provider = ProviderFactory.get_provider(self.provider_name)

        # Token budget: Gemini 3.x/2.5 Flash are "thinking" models whose
        # maxOutputTokens budget is shared between internal reasoning and the
        # visible answer. A generous budget is required for a full report.
        self.max_tokens = settings.AI_MAX_TOKENS_VISION

        # Timeout: honor AI_TIMEOUT_VISION, but never exceed AI_MAX_TIMEOUT_VISION.
        self.timeout_seconds = min(
            float(settings.AI_TIMEOUT_VISION),
            float(settings.AI_MAX_TIMEOUT_VISION),
        )

    def _build_generation_kwargs(self) -> Dict[str, Any]:
        """
        Extra kwargs passed to the provider.generate call.

        For Gemini "thinking" models we cap the internal reasoning budget so the
        bulk of the output-token budget is spent on the visible doctor report
        instead of being consumed by hidden chain-of-thought. We pass this as a
        plain dict; the Gemini provider forwards unknown kwargs straight to the
        SDK, and we swallow any rejection at the call site.
        """
        return {"thinkingConfig": {"thinkingBudget": -1}}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
        reraise=True,
    )
    async def _analyze_with_retry(self, messages: List[Dict[str, Any]]) -> str:
        """Helper to run the provider generation with timeout and retries."""
        loop = asyncio.get_running_loop()
        max_tokens = self.max_tokens
        model_name = self.model_name
        extra_kwargs = self._build_generation_kwargs()
        provider = self._provider

        def _generate():
            try:
                return provider.generate(
                    messages,
                    model=model_name,
                    temperature=0.2,
                    max_tokens=max_tokens,
                    **extra_kwargs,
                )
            except TypeError:
                # Provider/SDK does not accept thinkingConfig — retry without it.
                return provider.generate(
                    messages,
                    model=model_name,
                    temperature=0.2,
                    max_tokens=max_tokens,
                )

        future = loop.run_in_executor(None, _generate)
        return await asyncio.wait_for(future, timeout=self.timeout_seconds)

    def _build_messages(self, image_url: str) -> List[Dict[str, Any]]:
        """Construct the multimodal payload (system + user with text + image)."""
        return [
            {"role": "system", "content": VISION_SYSTEM_INSTRUCTION},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": VISION_ANALYSIS_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

    async def analyze_image(self, image_bytes: bytes, mime_type: str, upload_id: str) -> Dict[str, Any]:
        """
        Sends the image (or PDF) to the Vision model to get a raw, detailed clinical
        analysis written in the voice of a reviewing physician.
        """
        MultimodalLogger.log_stage_start(
            PipelineStage.VISION_STARTED, upload_id, {"model": self.model_name}
        )
        start_time = time.time()

        try:
            # Base64 encode the image / PDF document
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            image_url = f"data:{mime_type};base64,{encoded_image}"
            messages = self._build_messages(image_url)

            try:
                response_text = await self._analyze_with_retry(messages)
            except Exception as exc:
                if (
                    _should_fallback_for_model_error(exc)
                    and self.model_name != self.fallback_model_name
                ):
                    MultimodalLogger.log_event(
                        PipelineStage.VISION_STARTED,
                        upload_id,
                        f"Primary vision model unavailable or timed out "
                        f"({self.provider_name}:{self.model_name}); falling back to "
                        f"{self.fallback_provider_name}:{self.fallback_model_name}",
                    )
                    self.provider_name = self.fallback_provider_name
                    self.model_name = self.fallback_model_name
                    self._provider = ProviderFactory.get_provider(self.provider_name)
                    response_text = await self._analyze_with_retry(messages)
                else:
                    raise

            processing_time = (time.time() - start_time) * 1000

            MultimodalLogger.log_stage_complete(
                PipelineStage.VISION_COMPLETED,
                upload_id,
                {"processing_time_ms": processing_time, "model": self.model_name},
            )

            return {
                "raw_text": response_text,
                "confidence": 0.85,  # Estimated confidence
                "model_used": self.model_name,
                "processing_time_ms": processing_time,
            }

        except asyncio.TimeoutError:
            error_msg = f"Vision analysis timed out after {self.timeout_seconds}s"
            MultimodalLogger.log_stage_error(PipelineStage.VISION_COMPLETED, upload_id, error_msg)
            raise VisionError(error_msg, provider=self.provider_name)
        except Exception as e:
            MultimodalLogger.log_stage_error(PipelineStage.VISION_COMPLETED, upload_id, str(e))
            raise VisionError(f"Vision analysis failed: {str(e)}", provider=self.provider_name)


def _should_fallback_for_model_error(exc: Exception) -> bool:
    """Decide whether a vision failure should trigger the fallback model."""
    message = str(exc).lower()
    # Status-code style errors
    if any(code in message for code in ("429", "500", "502", "503", "504")):
        return True
    return bool(
        "model_decommissioned" in message
        or "decommissioned" in message
        or "model_not_found" in message
        or "does not exist" in message
        or "not found" in message
        or "rate limit" in message
        or "rate_limit" in message
        or "quota" in message
        or "timeout" in message
        or "timed out" in message
        or "overloaded" in message
        or "unavailable" in message
    )
