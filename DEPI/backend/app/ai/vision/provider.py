# backend/app/ai/vision/provider.py
# ─────────────────────────────────────────────────────────────────────────────
# Vision Provider
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.ai.vision.gemini_vision_provider import GeminiVisionProvider
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
    using Vision-Language Models (Gemini 3.5 Flash with current Gemini fallback models).
    Includes retries, generous timeouts, and a thinking-model-friendly token budget.
    """

    def __init__(self, provider_name: str | None = None, model_name: str | None = None):
        settings = get_settings()
        self.provider_name = provider_name or settings.PROVIDER_VISION
        self.model_name = model_name or settings.MODEL_VISION
        self.fallback_provider_name = "gemini"
        self.fallback_model_name = settings.MODEL_VISION_FALLBACK
        self.fallback_model_names = _dedupe_models(
            [
                settings.MODEL_VISION_FALLBACK,
                "gemini-3.1-flash-lite",
                "gemini-3.5-flash",
            ]
        )
        self._provider = GeminiVisionProvider(self.model_name)
        # Token budget: Gemini 3.x Flash models are "thinking" models whose
        # maxOutputTokens budget is shared between internal reasoning and the
        # visible answer. A generous budget is required for a full report.
        self.max_tokens = settings.AI_MAX_TOKENS_VISION

        # Timeout: honor AI_TIMEOUT_VISION, but never exceed AI_MAX_TIMEOUT_VISION.
        self.timeout_seconds = min(
            float(settings.AI_TIMEOUT_VISION),
            float(settings.AI_MAX_TIMEOUT_VISION),
        )

    # ------------------------------------------------------------------
    # FIX: _analyze_with_retry now takes the raw bytes + mime_type that
    # GeminiVisionProvider.analyze() actually needs.  Previously it
    # accepted a `messages` list that it never used, while the nested
    # _generate() closure tried (and failed) to reference `image_bytes`
    # and `mime_type` from analyze_image()'s call-stack frame — names
    # that are NOT in _analyze_with_retry's lexical scope and therefore
    # always raised NameError inside the executor thread.
    #
    # Five bugs fixed here:
    #  1. image_bytes / mime_type are now proper parameters — no more
    #     NameError inside the executor thread.
    #  2. _generate() now returns the result of provider.analyze() so
    #     the awaited future carries the actual text back.
    #  3. Signature now matches the fallback call site in analyze_image().
    #  4. Dead locals (max_tokens, model_name, extra_kwargs) removed.
    #  5. The messages / data-URL indirection is removed; raw bytes go
    #     straight to GeminiVisionProvider, matching the standalone path.
    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        # Only retry on transient network/connection errors.
        # asyncio.TimeoutError is intentionally excluded — a timeout means
        # the 45 s budget is already gone; retrying would triple the wait.
        retry=retry_if_exception_type(ConnectionError),
        reraise=True,
    )
    async def _analyze_with_retry(self, image_bytes: bytes, mime_type: str) -> str:
        """Run GeminiVisionProvider.analyze() in a thread with timeout and retries.

        GeminiVisionProvider.analyze() is synchronous (blocking network I/O).
        We offload it to the default ThreadPoolExecutor so the event loop is
        never blocked, then guard the whole call with asyncio.wait_for.
        """
        loop = asyncio.get_running_loop()
        provider = self._provider

        def _generate() -> str:
            # Both image_bytes and mime_type are captured from THIS function's
            # parameters — they are in the lexical scope of _generate's closure.
            return provider.analyze(
                image_bytes=image_bytes,
                mime_type=mime_type,
                system_prompt=VISION_SYSTEM_INSTRUCTION,
                user_prompt=VISION_ANALYSIS_PROMPT,
            )

        future = loop.run_in_executor(None, _generate)
        return await asyncio.wait_for(future, timeout=self.timeout_seconds)

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
            response_text = await self._analyze_with_fallbacks(
                image_bytes=image_bytes,
                mime_type=mime_type,
                upload_id=upload_id,
            )

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

    async def _analyze_with_fallbacks(self, image_bytes: bytes, mime_type: str, upload_id: str) -> str:
        # Pass raw bytes directly — no base64 / data-URL round-trip needed
        # because GeminiVisionProvider.analyze() accepts bytes natively.
        try:
            return await self._analyze_with_retry(image_bytes, mime_type)
        except Exception as primary_exc:
            if not _should_fallback_for_model_error(primary_exc):
                raise

            failed_models = {self.model_name}
            last_exc: Exception = primary_exc

            for fallback_model in self.fallback_model_names:
                if fallback_model in failed_models:
                    continue

                MultimodalLogger.log_event(
                    PipelineStage.VISION_STARTED,
                    upload_id,
                    f"Vision model unavailable ({self.provider_name}:{self.model_name}); "
                    f"falling back to {self.fallback_provider_name}:{fallback_model}",
                )
                self.provider_name = self.fallback_provider_name
                self.model_name = fallback_model
                self._provider = GeminiVisionProvider(fallback_model)

                try:
                    return await self._analyze_with_retry(image_bytes, mime_type)
                except Exception as fallback_exc:
                    last_exc = fallback_exc
                    failed_models.add(fallback_model)
                    if not _should_fallback_for_model_error(fallback_exc):
                        raise

            raise last_exc


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
        or "no longer available" in message
    )


def _dedupe_models(models: list[str]) -> list[str]:
    result: list[str] = []
    for model in models:
        if model and model not in result:
            result.append(model)
    return result
