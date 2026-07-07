# 🏥 MedCortex — AI-Powered Clinical Knowledge Assistant

<div align="center">

![MedCortex Banner](https://img.shields.io/badge/MedCortex-AI%20Health%20Assistant-6f4ef2?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyek0xMyAxN0gxMXYtNkg3bDUtNSA1IDVoLTR2NnoiLz48L3N2Zz4=)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-00B6A1?style=flat-square)](https://pinecone.io)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat-square)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-3.5%20Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

**A full-stack AI-powered medical assistant combining RAG knowledge retrieval, multimodal vision analysis, and speech-to-text capabilities. Grounded in NIH MedlinePlus data and clinical textbooks with cited, verifiable sources.**

[Features](#-features) · [Architecture](#-system-architecture) · [Data Pipeline](#-data-pipeline) · [Backend](#-backend) · [Frontend](#-frontend) · [Getting Started](#-getting-started)

</div>

---

## 📌 Overview

MedCortex is a comprehensive **AI-powered clinical knowledge system** that integrates multiple AI capabilities:

- **RAG (Retrieval-Augmented Generation)** for answering clinical questions from NIH MedlinePlus and medical textbooks
- **Multimodal Vision Analysis** using Gemini 3.5 Flash for interpreting lab reports, prescriptions, and medical documents
- **Speech-to-Text** using Whisper Large V3 Turbo for voice input
- **Structured Medical Parsing** for extracting patient data, medications, diagnoses, and lab values
- **Doctor Recommendations** with Egypt-specific clinic/doctor search via Google Maps API

The system uses a **FastAPI backend** with a **Next.js 14 frontend**, featuring JWT authentication, conversation history, and a polished UI.

> ⚠️ **Disclaimer:** MedCortex is intended for educational and research purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Dual Knowledge Base** | NIH MedlinePlus API (4,822 chunks) + 4 curated medical textbooks (9,513 vectors) |
| 👁️ **Vision Analysis** | Gemini 3.5 Flash for lab reports, prescriptions, and medical document interpretation |
| � **Medical Image Analyzer** | Groq Vision models for wound/skin condition analysis with HuggingFace fallback |
| �🎤 **Speech-to-Text** | Whisper Large V3 Turbo for voice input transcription |
| 📊 **Structured Parsing** | Extract patient info, medications, diagnoses, lab values from documents |
| 🧠 **High-Dimensional Embeddings** | `BAAI/bge-large-en-v1.5` producing 1024-dimension vectors for precise semantic search |
| ⚡ **Fast Inference** | Llama 3.3 70B via Groq + Gemini 3.5 Flash for vision tasks |
| 🎯 **Cited Answers** | Every response cites the exact book and section the information came from |
| 🚫 **No Hallucinations** | Strictly grounded — refuses to answer if the context doesn't contain the answer |
| 👨‍⚕️ **Doctor Recommendations** | Egypt-specific clinic/doctor search with Google Maps integration |
| 🏥 **Hospital Search** | Location-based hospital search using Egyptian hospitals database |
| 💊 **Pre-computed tabs** | Parallel preloaded Specialist tabs (Drugs, Nutrition, Rehab) using optimized 8B models |
| 🔐 **Full Auth System** | JWT-based login/signup with optional Google OAuth |
| 💬 **Conversation History** | Persistent chat sessions with message history and preloaded clinical plans |
| 🎨 **Premium UI/Dashboard** | Glassmorphism dashboard with progress timelines, metrics, and animated wave layouts |

---

## 🏛️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MedCortex System                                  │
├──────────────────────────────┬──────────────────────────────────────────────┤
│        DATA PIPELINE         │              INFERENCE PIPELINE              │
│                              │                                              │
│  NIH MedlinePlus API         │  User Query (Text/Voice/Image)               │
│         ↓                    │       ↓                                      │
│  Alphabet Sweep (A-Z)        │  ┌─────────────────────────────────────┐     │
│     300 topics/letter        │  │ Input Type Detection                │     │
│         ↓                    │  └─────────────────────────────────────┘     │
│  Sentence Chunker            │       ↓                                      │
│  (512 chars, 80 OL)          │  ┌──────────┬──────────┬──────────────┐      │
│         ↓                    │  │   Text   │  Image   │    Audio     │      │
│  Dedup + Clean               │  └────┬─────┴────┬─────┴──────┬───────┘      │
│  4,822 unique chunks         │       ↓          ↓            ↓              │
│         ↓                    │  BGE Embedder  Vision     Whisper            │
│  4 Medical Textbooks         │  (1024d)      Provider   Transcribe          │
│  (9,513 vectors)             │       ↓          ↓            ↓              │
│         ↓                    │  Pinecone     Gemini        Text             │
│  Pinecone Index              │  MMR Search   Analysis      Input            │
│  (1024d, cosine)             │       ↓          ↓           ↓               │
│                              │  ┌─────────────────────────────────────┐     │
│                              │  │        Unified Context              │     │
│                              │  │  - Vision Output                    │     │
│                              │  │  - Structured Data                  │     │
│                              │  │  - Retrieved Context                │     │
│                              │  └─────────────────────────────────────┘     │
│                              │       ↓                                      │
│                              │  Llama 3.3 70B (Groq API)                    │
│                              │       ↓                                      │
│                              │  Structured Answer + Citations               │
│                              │  + Doctor Recommendations                    │
└──────────────────────────────┴──────────────────────────────────────────────┘
```

---

## 📚 Data Pipeline

### Source 1 — NIH MedlinePlus (Structured)

The structured pipeline fetches every health topic from the [NIH MedlinePlus API](https://wsearch.nlm.nih.gov/ws/query) using a full **alphabet sweep** (A–Z, 300 results per letter).

```python
# Alphabet sweep → 26 queries × 300 topics each
QUERIES = [(letter, 300) for letter in string.ascii_lowercase]
```

**Final dataset stats after cleaning:**

| Metric | Value |
|---|---|
| Raw chunks fetched | 12,016 |
| After deduplication | 4,843 |
| After text-dedup | **4,822** |
| Unique health topics | **772** |
| Columns retained | 15 |
| File size | 37.45 MB |

**Schema overview:**

```
Vector Core   → chunk_id, doc_id, text, embedding_text
Mechanics     → chunk_index, chunk_total
Metadata      → topic_id, title, synonyms, mesh_terms, disease_category
Display       → full_summary, snippet, source_url
Auditing      → data_source, search_term
```

**Chunking strategy:**
- Sentence-aware splitting at `.`, `!`, `?` boundaries
- Chunk size: **512 characters** with **80-character overlap**
- Each chunk inherits full document metadata for filtered retrieval

**Cleaning steps:**
1. Drop columns with 100% missing values (`research_institute`, `date_created`, `date_updated`, `language`, `see_also`)
2. Convert fake empty strings (`""`, `"—"`) to `NaN`
3. Impute remaining nulls: `synonyms` (784 rows), `mesh_terms` (12 rows) → `"Unknown"`
4. Deduplicate on `chunk_id` then on `text`

---

### Source 2 — Medical Textbooks (Unstructured)

Four clinical textbooks processed with **Docling** into LangChain `Document` objects with rich metadata:

| Book | Chunks |
|---|---|
| Gray's Anatomy for Students (4th Ed.) | 2,676 |
| Mosby's Diagnostic & Laboratory Test Reference (15th Ed.) | 3,301 |
| Learning Radiology: Recognizing the Basics (3rd Ed.) | 1,310 |
| Symptoms to Diagnosis | 2,226 |
| **Total** | **9,513** |

Each chunk carries: `book_title`, `source_file`, `docling_headings`, `page_content`.

---

### Pinecone Vector Store

```python
INDEX_NAME = "medical-assistant"
DIMENSION  = 1024          # BAAI/bge-large-en-v1.5
METRIC     = "cosine"
NAMESPACE  = "medical_textbooks_base"
CLOUD      = "aws"
REGION     = "us-east-1"
```

Embeddings are computed on GPU in batches of 100 using `langchain-huggingface` + `langchain-pinecone`.

---

## 🔧 Backend

Built with **FastAPI** and organized into modular components:

### Project Structure

```
backend/
├── app/
│   ├── ai/
│   │   ├── providers/          # AI provider implementations
│   │   │   ├── base.py        # Base provider interfaces
│   │   │   ├── groq_provider.py    # Groq (Llama models)
│   │   │   ├── gemini_provider.py  # Gemini (Vision models)
│   │   │   ├── model_registry.py   # Model registry
│   │   │   └── provider_factory.py # Provider factory
│   │   ├── prompts/            # Prompt templates
│   │   │   └── vision_prompts.py   # Doctor-persona vision prompts
│   │   ├── vision/             # Vision analysis
│   │   │   ├── provider.py     # Vision provider wrapper
│   │   │   └── service.py      # Vision service orchestration
│   │   ├── multimodal/         # Multimodal processing
│   │   │   ├── router.py       # Input routing (PDF → Vision, Image → Vision)
│   │   │   ├── preprocessing.py # Image preprocessing
│   │   │   └── schemas.py      # Pydantic schemas
│   │   ├── shared/             # Shared utilities
│   │   │   └── medical_parser.py # Structured medical text parsing
│   │   └── clinical/           # Clinical tools
│   │       └── lab_interpreter.py # Lab value interpretation
│   ├── api/                    # API routes
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── chat.py             # Chat/conversation endpoints
│   │   ├── upload.py           # File upload endpoint
│   │   ├── transcribe.py       # Speech-to-text endpoint
│   │   ├── conversations.py    # Conversation management
│   │   ├── messages.py         # Message persistence
│   │   └── history.py          # Chat history
│   ├── config/                 # Configuration
│   │   └── settings.py         # Centralized settings
│   ├── database/               # Database
│   │   └── database.py         # SQLAlchemy setup
│   └── models/                 # SQLAlchemy models
│       ├── user.py
│       ├── conversation.py
│       └── message.py
├── tests/                      # Test suite
│   └── api/
│       └── test_upload_pipeline.py
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── main.py                     # FastAPI application entry
```

### Key Components

#### AI Providers

- **GroqProvider**: Wraps LangChain's ChatGroq for Llama 3.3 70B, Llama 3.1 70B, and other Groq models
- **GeminiProvider**: Wraps Google Gen AI SDK for Gemini 3.5 Flash and 2.5 Flash (vision)
- **ModelRegistry**: Central registry for all available AI models

#### Vision Pipeline

- **DefaultRouter**: Routes PDFs and images to Vision processor (Gemini)
- **VisionProvider**: Handles image analysis with configurable token limits and timeouts
- **VisionService**: Orchestrates vision analysis and structured medical parsing
- **SharedMedicalParser**: Extracts structured data (patient, medications, diagnoses, labs) from vision output

#### Multimodal Processing

- **DefaultPreprocessor**: Resizes oversized images, handles format conversion
- **ProcessingContext**: Unified context for multimodal processing pipeline
- **UnifiedMedicalContext**: Aggregates vision output, OCR output, and structured data

#### API Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/signup` - User registration
- `POST /chat` - Send message and get AI response
- `POST /upload` - Upload medical documents (PDF, images)
- `POST /transcribe` - Transcribe audio to text
- `GET /conversations` - List user conversations
- `GET /conversations/{id}/messages` - Get conversation history

### Configuration

Key settings in `app/config/settings.py`:

```python
# AI Models
MODEL_CHAT = "llama-3.3-70b-versatile"
MODEL_VISION = "gemini-3.5-flash"
MODEL_VISION_FALLBACK = "gemini-2.5-flash"

# Vision-specific settings
AI_MAX_TOKENS_VISION = 16384
AI_TIMEOUT_VISION = 45.0
AI_MAX_TIMEOUT_VISION = 90.0

# Providers
PROVIDER_CHAT = "groq"
PROVIDER_VISION = "gemini"
PROVIDER_EMBEDDING = "huggingface"

# Database
DATABASE_URL = "sqlite:///./medcortex.db"

# Pinecone
PINECONE_API_KEY
PINECONE_INDEX_NAME = "medical-assistant"

# Groq
GROQ_API_KEY

# Gemini
GEMINI_API_KEY
```

---

## 🎨 Frontend

Built with **Next.js 14 (App Router)** + **TypeScript** + **Tailwind CSS**, featuring a distinct visual identity in purple/violet (`#6f4ef2`).

### Project Structure

```
frontend/
├── app/
│   ├── login/
│   │   └── page.tsx          # Login page with AuthWaveLayout
│   ├── signup/
│   │   └── page.tsx          # Signup page with AuthWaveLayout
│   ├── chat/
│   │   └── page.tsx          # Main chat interface
│   └── api/
│       └── transcribe/
│           └── route.ts     # Speech-to-text proxy
├── components/
│   ├── auth/
│   │   ├── AuthWaveLayout.tsx      # Animated SVG wave layout
│   │   ├── AuthSplitLayout.tsx     # Hero image split layout
│   │   ├── LoginForm.tsx           # Email/password form
│   │   ├── SignupForm.tsx          # Registration form
│   │   ├── FloatingField.tsx       # Floating label input
│   │   └── GoogleSignInButton.tsx # Google OAuth
│   ├── chat/
│   │   ├── ChatWorkspace.tsx       # Main chat workspace
│   │   ├── ResponseCard.tsx        # Response display with tabs
│   │   ├── VoiceButton.tsx         # Speech-to-text button
│   │   └── UploadButton.tsx       # File upload button
│   └── ui/                      # Reusable UI components
├── hooks/
│   ├── useSpeechToText.ts      # Speech-to-text hook
│   └── useDoctorRecommendations.ts # Doctor search hook
├── lib/
│   ├── extractDoctorReferral.ts # Extract doctor info from text
│   └── utils.ts                 # Utility functions
├── services/
│   └── chat.ts                  # Chat API client
└── types/
    └── chat.ts                  # TypeScript types
```

### Key Features

#### Authentication

- JWT-based authentication with access tokens
- Email/password login and signup
- Google One Tap OAuth integration
- Session persistence in localStorage

#### Chat Interface

- Real-time streaming responses
- Message history with conversation persistence
- Tabbed response display (Diagnosis, Lifestyle, Doctors, Sources)
- Markdown rendering with table support
- Voice input with Whisper transcription
- File upload for medical documents (PDF, images)

#### Document Analysis

- Upload lab reports, prescriptions, and medical documents
- Vision analysis via Gemini 3.5 Flash
- Structured parsing of extracted data
- Display of doctor's review, lab results, medications, and diagnoses

#### Doctor Recommendations

- Egypt-specific clinic/doctor search
- Google Maps integration for nearby results
- Display of doctor details, ratings, and contact info

### Design Highlights

- **AuthWaveLayout** — SVG blob/wave decorations with depth layers, glassmorphism card
- **Pill inputs** — gradient icon badges, floating labels, purple focus rings
- **Gradient CTAs** — `from-[#8566FF] to-[#6f4ef2]` with lift-on-hover shadow
- **Fully responsive** — single column on mobile, dual column on desktop
- **Dark mode support** — Consistent theming across components

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- GPU (recommended for embedding generation)
- Pinecone account (free tier works)
- Groq API key (free at [console.groq.com](https://console.groq.com))
- Gemini API key (free at [ai.google.dev](https://ai.google.dev))
- Google Maps API key (for doctor recommendations)

### 1. Clone the repo

```bash
git clone https://github.com/AliySoliman/Medical-Chatbot
cd Medical-Chatbot-main/DEPI
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./medcortex.db

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX_NAME=medical-assistant

# Groq
GROQ_API_KEY=your-groq-api-key

# Gemini
GEMINI_API_KEY=your-gemini-api-key

# JWT Secret
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Run the backend:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create `.env.local` file in the frontend directory:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id   # Optional, for Google OAuth
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-key # For doctor recommendations
```

Run the frontend:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Data Pipeline (Optional)

To populate the Pinecone vector database with NIH MedlinePlus and medical textbook data, run the data pipeline notebooks in Google Colab (recommended for GPU acceleration):

```bash
pip install langchain langchain-core langchain-community langchain-groq \
            langchain-pinecone langchain-huggingface pinecone-client \
            sentence-transformers gradio docling
```

Set your API keys:
```python
import os
os.environ["PINECONE_API_KEY"] = "your-pinecone-key"
os.environ["GROQ_API_KEY"]     = "your-groq-key"
```

Run the notebooks in order:
1. `Copy_of_medical_assis_structure_API.ipynb` — Fetch & clean MedlinePlus data
2. `Copy_of_medical_assistant_rag.ipynb` — Embed textbooks → Pinecone → RAG demo

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI 0.104+ |
| **Frontend Framework** | Next.js 14 (App Router) |
| **Language** | Frontend: TypeScript 5.0+, Backend: Python 3.10+ |
| **LLM (Chat)** | Llama 3.3 70B via Groq API |
| **LLM (Vision)** | Gemini 3.5 Flash, Gemini 2.5 Flash via Google Gen AI |
| **Speech-to-Text** | Whisper Large V3 Turbo via Groq API |
| **Embeddings** | BAAI/bge-large-en-v1.5 (1024d) |
| **Vector DB** | Pinecone (Serverless, AWS us-east-1) |
| **RAG Framework** | LangChain (LCEL) |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Authentication** | JWT + Google One Tap OAuth |
| **Styling** | Tailwind CSS |
| **Data Source 1** | NIH MedlinePlus Web Services API |
| **Data Source 2** | Docling PDF parser (clinical textbooks) |
| **Doctor Search** | Google Maps Places API |
| **HTTP Client** | Axios (frontend), httpx (backend) |

---

## 📊 Performance

| Metric | Value |
|---|---|
| Total vectors in Pinecone | 9,513 |
| Embedding dimensions | 1,024 |
| Retrieval strategy | MMR (k=4, fetch_k=10) |
| Average chat response time | ~2–4 seconds |
| Vision analysis timeout | 45s (max 90s) |
| Vision max tokens | 16,384 |
| Knowledge base topics | 772 unique NIH topics |
| Medical textbooks indexed | 4 |

---

## 🔮 Roadmap

- [x] Parallel Specialist Branches (Drugs, Nutrition, Rehab)
- [x] Drug interaction checker module
- [x] Geographically aware Egypt-specific doctor recommendations
- [ ] Add structured NIH MedlinePlus chunks to Pinecone (separate namespace)
- [ ] Implement hybrid search (dense + sparse BM25)
- [ ] Add multi-turn conversation memory with context retention
- [ ] Symptom checker with differential diagnosis scoring
- [ ] Mobile app (React Native)
- [ ] Fine-tuned medical embedding model
- [ ] Real-time collaboration features
- [ ] Integration with electronic health records (EHR) systems
- [ ] Multi-language support (Arabic, French)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

```bash
# Fork → clone → create a branch
git checkout -b feature/your-feature-name

# Make changes, then
git commit -m "feat: add your feature"
git push origin feature/your-feature-name
# Open a Pull Request
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- [NIH MedlinePlus](https://medlineplus.gov/) for the open health topics API
- [BAAI](https://huggingface.co/BAAI/bge-large-en-v1.5) for the BGE embedding model
- [Groq](https://groq.com/) for ultra-fast Llama 3 inference
- [Google](https://ai.google.dev/) for Gemini vision models
- [Pinecone](https://pinecone.io/) for the serverless vector database
- [LangChain](https://langchain.com/) for the RAG orchestration framework
- [FastAPI](https://fastapi.tiangolo.com/) for the modern Python web framework
- [Next.js](https://nextjs.org/) for the React framework

---

<div align="center">
  <sub>Built with ❤️ for educational and research purposes · Not a substitute for professional medical advice</sub>
</div>
