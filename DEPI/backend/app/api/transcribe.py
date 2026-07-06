# backend/app/api/transcribe.py
# ─────────────────────────────────────────────────────────────────────────────
# Audio Transcription API
# POST /transcribe → Transcribe audio using Groq's Whisper model
# ─────────────────────────────────────────────────────────────────────────────

import logging
from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.ai.providers.provider_factory import ProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transcribe", tags=["Transcription"])


@router.post("", status_code=status.HTTP_200_OK)
async def transcribe_audio(file: UploadFile):
    """
    Transcribe audio file using Groq's Whisper model (whisper-large-v3-turbo).
    
    Accepts audio files in webm, ogg, mp3, wav, m4a formats.
    Returns transcribed text.
    """
    try:
        # Read file content
        audio_bytes = await file.read()
        
        if not audio_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file",
            )
        
        # Get Groq provider
        provider = ProviderFactory.get_provider("groq")
        
        # Transcribe audio
        text = provider.transcribe_audio(
            audio_file=audio_bytes,
            filename=file.filename or "audio.webm",
            model="whisper-large-v3-turbo",
            language="en",
        )
        
        return JSONResponse(content={"text": text})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Transcription error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {str(e)}",
        )
