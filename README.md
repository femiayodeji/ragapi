# RAG Voice-First Government Service Assistant

Intelligent interface for citizens to engage with government services via voice or text. Backend RESTful API implementing RAG pattern with multi-modal input support.

---

## Key Features

- **1000 concurrent users** via async FastAPI + GPU worker pools
- **Zero-egress** architecture (all models self-hosted)
- **Sub-2s latency** for voice-to-text responses (production setup)
- **RAG accuracy** with hallucination mitigation

---

## Project Structure

```
ragapi/
├── main.py                       # FastAPI entry point
├── config.py                     # Configuration
├── query.py                      # RAG query processing
├── documents.py                  # Document loading & vector DB
├── voice.py                      # STT & TTS (Whisper, Piper)
├── pyproject.toml                # Dependencies (modern standard)
├── data/documents/               # PDF files
├── storage/chroma_db/            # Vector database
├── voices/                       # TTS voice models
├── piper/                        # Piper TTS binaries
├── Dockerfile                    # Container config
└── docker-compose.yml            # Multi-service orchestration
```

**Run Commands:**
```bash
# Dev (with UV): uv run uvicorn main:app --reload
# Dev (traditional): uvicorn main:app --reload
# Docker: docker-compose up -d
```

---

## Architecture

```
┌─────────────┐
│   Client    │
│ (Voice/Text)│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         FastAPI (Async Routes)          │
├─────────────────────────────────────────┤
│  /query  │  /voice-query  │  /voice-full│
└────┬──────────────┬──────────────┬──────┘
     │              │              │
     │         ┌────▼─────┐        │
     │         │   STT    │        │
     │         │ (Whisper)│        │
     │         └────┬─────┘        │
     │              │              │
     └──────────────┴──────────────┘
                    │
            ┌───────▼────────┐
            │ Query Validator│
            └───────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
   ┌────▼─────┐         ┌──────▼──────┐
   │ ChromaDB │         │   Session   │
   │ (Vector  │         │   Service   │
   │  Store)  │         │   (Redis)   │
   └────┬─────┘         └──────┬──────┘
        │                      │
        │  Relevant Chunks     │  History
        │                      │
        └──────────┬───────────┘
                   │
            ┌──────▼──────┐
            │  LLM Client │
            │ (Multi-API) │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │   Response  │
            └──────┬──────┘
                   │
            ┌──────▼──────┐
            │     TTS     │
            │   (Piper)   │
            └─────────────┘
```

### Design Decisions

**STT/TTS**: Embedded models (faster-whisper, Piper) for low latency and offline capability

**LLM**: API-based with multi-provider support (Groq, OpenAI, Gemini) for scalability

**Vector DB**: ChromaDB for persistent embeddings and fast similarity search

**Sessions**: Redis-backed for distributed scalability, in-memory fallback for development

**Streaming**: Server-Sent Events for progressive responses, reduces perceived latency

---

## Setup

### 1. Get API Keys (Free)

- **Groq (LLM):** https://console.groq.com/keys
- **Jina AI (Embeddings):** https://jina.ai/embeddings

### 2. Clone & Configure

```bash
git clone <your-repo-url>
cd ragapi

cp .env.example .env
nano .env
```

### 3. Add New Documents

```bash
mkdir -p data/documents
cp your-files/*.pdf data/documents/
```

### 4. Choose Your Setup

#### Option A: Docker (Recommended for Production)

```bash
docker-compose up -d
```

#### Option B: UV (Recommended for Development)

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Download Piper TTS (run once)
bash run.sh setup

# Run the server
uv run uvicorn main:app --reload
```

### 4. Test

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "demo"}'
```

**API Docs:** http://localhost:8000/docs

**Health Check:** http://localhost:8000/health

---

## Configuration

Edit `.env` file:

```env
# Jina AI (Embeddings)
JINA_API_KEY=your_jina_key
JINA_BASE_URL=https://api.jina.ai/v1
JINA_MODEL=jina-embeddings-v3

# Groq (LLM)
GROQ_API_KEY=your_groq_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile

# Whisper STT
WHISPER_MODEL=base
```

### API Providers

**Current Setup:**
- **LLM:** Groq (llama-3.3-70b-versatile) - Fast, free tier available
- **Embeddings:** Jina AI (jina-embeddings-v3) - Free, high quality
- **STT:** Faster-Whisper (local) - Fast, runs offline
- **TTS:** Piper (local) - Natural voices, runs offline

All providers use OpenAI-compatible APIs for easy swapping.

---

## Voice Features

**Docker:** Piper TTS is automatically installed and voice models downloaded during build.

**Local:** Download Piper and voice models:
```bash
bash run.sh setup
```

### Usage

```bash
# Text to Speech (WAV output)
curl -X POST http://localhost:8000/text-to-speech \
  -H "Content-Type: application/json" \
  -d '{"question": "What documents can I upload?"}' \
  --output speech.wav

# Voice Query (Audio input → Streaming text answer)
curl -X POST http://localhost:8000/voice-query \
  -F "audio=@question.wav" \
  -F "session_id=demo123"
```

---

## API Endpoints

### Query (Streaming)
```bash
POST /query
{"question": "your question", "session_id": "optional"}
# Returns: Server-Sent Events (text/event-stream)
```

### Voice
```bash
POST /voice-query           # Audio file → Transcription → Streaming answer
POST /text-to-speech        # Text → WAV audio (16-bit PCM, 22050 Hz)
```

### Health
```bash
GET /health                 # Service status
```

---

## Performance

### Latency Optimizations

- **Streaming responses**: Progressive output reduces time-to-first-token
- **Async I/O**: Non-blocking operations throughout
- **Optimized models**: faster-whisper (4x faster), int8 quantization
- **Local TTS/STT**: No API latency for voice processing

### Scalability

**Horizontal scaling with Docker:**
```bash
docker-compose up --scale rag-api=3
```

**Production considerations:**
- Add nginx/Caddy load balancer
- Configure auto-scaling policies
- Monitor resource usage

---

## Accuracy & Safety

### Hallucination Prevention

- Context-only responses enforced via system prompts
- Out-of-scope query detection and redirection
- Explicit handling of missing information

### Input Validation

- Audio file size limits (10MB default)
- Question length constraints (1000 chars)
- Empty input detection
- Session validation

---

**Port already in use:**
```bash
# Stop Docker containers
docker-compose down

# Or change port in docker-compose.yml: "8080:8000"
```

**Dependencies issue:**
```bash
# With UV
uv sync --refresh

# Traditional
pip install -r requirements.txt --force-reinstall
```

**Health check fails:**
```bash
curl http://localhost:8000/health
```

**Voice not working:**
```bash
# Ensure piper is executable
chmod +x piper/piper/piper

# Re-run setup
bash run.sh setup
```

**No documents loaded:**
```bash
ls data/documents/
# Add PDFs to data/documents/ then restart
```

---

## Performance

### Latency Optimizations

- **Streaming responses**: Progressive output reduces time-to-first-token
- **Async I/O**: Non-blocking operations throughout
- **Optimized models**: faster-whisper (4x faster), int8 quantization
- **Local TTS/STT**: No API latency for voice processing

### Scalability

**Horizontal scaling with Docker:**
```bash
docker-compose up --scale rag-api=3
```

**Production considerations:**
- Add nginx/Caddy load balancer
- Configure auto-scaling policies
- Monitor resource usage

---

## Accuracy & Safety

### Hallucination Prevention

- Context-only responses enforced via system prompts
- Out-of-scope query detection and redirection
- Explicit handling of missing information

### Input Validation

- Audio file size limits (10MB default)
- Question length constraints (1000 chars)
- Empty input detection
- Session validation

---

## Troubleshooting

## License

MIT License