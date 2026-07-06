# backend/app/ai/ocr/provider.py
# ─────────────────────────────────────────────────────────────────────────────
# Robust OCR Extractor (Handles Fallbacks, Retries, Timeouts)
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.ai.ocr.factory import OCRProviderFactory
from app.ai.ocr.models import OCRExtractionResult
from app.ai.multimodal.exceptions import ExtractionError
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage


class RobustOCRExtractor:
    """
    Manages OCR extraction with fallback strategies, retries, and timeouts 
    to ensure high availability. Never crashes the workflow if a provider fails.
    """
    
    def __init__(self, primary: str = "paddleocr", fallbacks: List[str] = None):
        self.primary_provider_name = primary
        self.fallback_names = fallbacks or ["easyocr"]
        self.timeout_seconds = 15.0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
        reraise=True
    )
    async def _extract_with_retry_and_timeout(self, provider_name: str, image_bytes: bytes) -> OCRExtractionResult:
        """Helper to run extraction with timeout and retry logic."""
        provider = OCRProviderFactory.get_provider(provider_name)
        if not provider.is_available():
            raise ValueError(f"{provider_name} is unavailable")
            
        # Run the provider extraction with a strict timeout
        return await asyncio.wait_for(provider.extract_text(image_bytes), timeout=self.timeout_seconds)
        
    async def extract(self, image_bytes: bytes, upload_id: str) -> OCRExtractionResult:
        MultimodalLogger.log_stage_start(PipelineStage.OCR_STARTED, upload_id, {"primary": self.primary_provider_name})
        
        providers_to_try = [self.primary_provider_name] + self.fallback_names
        last_error = None
        
        for provider_name in providers_to_try:
            try:
                # Use the resilient wrapper method
                result = await self._extract_with_retry_and_timeout(provider_name, image_bytes)
                
                # Mark if fallback was used
                if provider_name != self.primary_provider_name:
                    result.warnings.append(f"Primary OCR failed. Fallback '{provider_name}' was used.")
                    
                MultimodalLogger.log_stage_complete(
                    PipelineStage.OCR_COMPLETED,
                    upload_id,
                    {"provider_used": provider_name, "confidence": result.average_confidence}
                )
                return result
                
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Provider {provider_name} timed out after {self.timeout_seconds} seconds")
                MultimodalLogger.log_event(
                    PipelineStage.OCR_STARTED,
                    upload_id,
                    str(last_error),
                    is_error=True
                )
            except Exception as e:
                last_error = e
                MultimodalLogger.log_event(
                    PipelineStage.OCR_STARTED,
                    upload_id,
                    f"Provider {provider_name} failed: {str(e)}",
                    is_error=True
                )
                
        # If all providers fail
        error_msg = f"All OCR providers failed. Last error: {str(last_error)}"
        MultimodalLogger.log_stage_error(PipelineStage.OCR_COMPLETED, upload_id, error_msg)
        raise ExtractionError(error_msg, provider="All")
