import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load env files before any code reads os.environ (Groq, Pinecone, etc.).
# Order: later files override earlier. Only files that exist are loaded.
_backend_root = Path(__file__).resolve().parent.parent
_repo_root = _backend_root.parent
for _env_path in (
    _repo_root / ".env",
    Path.cwd() / ".env",
    _backend_root / ".env",
    _backend_root / ".env.local",
):
    if _env_path.is_file():
        load_dotenv(_env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.database.database import Base, engine
import app.models  # noqa: F401
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.api.messages import router as messages_router
from app.api.history import router as history_router
from app.api.upload import router as upload_router
from app.api.transcribe import router as transcribe_router
from app.api.egyptian_doctors import router as egyptian_doctors_router
from app.api.egyptian_hospitals import router as egyptian_hospitals_router
from app.api.drugs import router as drugs_router
from app.api.nutrition import router as nutrition_router
from app.api.rehab import router as rehab_router

settings = get_settings()
app = FastAPI(title="MedCortex API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.ngrok-free\.(dev|app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    if not os.getenv("GROQ_API_KEY"):
        logging.getLogger("uvicorn.error").warning(
            "GROQ_API_KEY is missing. Put it in backend/.env (copy from .env.example). "
            "Keys in .env.example are NOT loaded — the file must be named .env"
        )
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(history_router)
app.include_router(upload_router)
app.include_router(transcribe_router)
app.include_router(egyptian_doctors_router)
app.include_router(egyptian_hospitals_router)
app.include_router(drugs_router)
app.include_router(nutrition_router)
app.include_router(rehab_router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
