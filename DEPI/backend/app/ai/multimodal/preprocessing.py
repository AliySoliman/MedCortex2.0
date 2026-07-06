# backend/app/ai/multimodal/preprocessing.py
# ─────────────────────────────────────────────────────────────────────────────
# Multimodal Preprocessing
# ─────────────────────────────────────────────────────────────────────────────

from io import BytesIO
from math import sqrt

from PIL import Image, ImageOps

from app.ai.multimodal.interfaces import BasePreprocessor
from app.ai.multimodal.schemas import ProcessingContext
from app.ai.multimodal.logger import MultimodalLogger, PipelineStage


MAX_VISION_PIXELS = 30_000_000
MAX_VISION_DIMENSION = 6000


class DefaultPreprocessor(BasePreprocessor):
    """
    Default preprocessor.
    Applies standard enhancements to images or passes documents through.
    """
    
    async def preprocess(self, context: ProcessingContext) -> bytes:
        MultimodalLogger.log_stage_start(PipelineStage.PREPROCESSING_STARTED, context.upload_id)
        
        try:
            # Normalise oversized images before sending them to vision models.
            if str(context.mime_type or "").startswith("image/"):
                processed_bytes = _resize_image_if_needed(context.file_bytes, context.upload_id)
            else:
                # Documents such as PDFs are passed through to OCR unchanged.
                processed_bytes = context.file_bytes
            
            MultimodalLogger.log_stage_complete(
                PipelineStage.PREPROCESSING_COMPLETED,
                context.upload_id,
                {"original_size": len(context.file_bytes), "processed_size": len(processed_bytes)}
            )
            return processed_bytes
            
        except Exception as e:
            MultimodalLogger.log_stage_error(PipelineStage.PREPROCESSING_COMPLETED, context.upload_id, str(e))
            raise


def _resize_image_if_needed(image_bytes: bytes, upload_id: str) -> bytes:
    """
    Downscale large medical photos so they stay within vision model limits.

    Groq vision models reject very large images by pixel count, so we cap the
    total pixels and long edge before forwarding the upload downstream.
    """
    with Image.open(BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        width, height = image.size
        pixel_count = width * height

        if pixel_count <= MAX_VISION_PIXELS and max(width, height) <= MAX_VISION_DIMENSION:
            return image_bytes

        scale = min(
            sqrt(MAX_VISION_PIXELS / float(pixel_count)),
            MAX_VISION_DIMENSION / float(max(width, height)),
        )
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        output = BytesIO()
        original_format = (image.format or "").upper()
        save_format = original_format if original_format in {"JPEG", "JPG", "PNG", "WEBP"} else "JPEG"

        if save_format in {"JPEG", "JPG"} and resized.mode not in ("RGB", "L"):
            resized = resized.convert("RGB")

        if save_format == "JPEG" and resized.mode == "RGBA":
            background = Image.new("RGB", resized.size, (255, 255, 255))
            background.paste(resized, mask=resized.getchannel("A"))
            resized = background

        save_kwargs = {"quality": 90, "optimize": True} if save_format == "JPEG" else {}
        resized.save(output, format=save_format, **save_kwargs)

        MultimodalLogger.log_event(
            PipelineStage.PREPROCESSING_COMPLETED,
            upload_id,
            f"Resized image from {width}x{height} to {new_width}x{new_height} for vision safety.",
            {"original_pixels": pixel_count, "resized_pixels": new_width * new_height},
        )
        return output.getvalue()
