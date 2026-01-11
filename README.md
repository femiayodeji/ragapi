# RAG Voice-First Government Service Assistant

Intelligent interface for citizens to engage with government services via voice or text. Backend RESTful API implementing RAG pattern with multi-modal input support.

---

## Project Structure

```
ragapi/
├── app/                          # Main application
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Configuration
│   ├── models.py                 # Pydantic models
│   ├── api/                      # API routes
│   ├── services/                 # STT, TTS, documents, sessions
│   ├── clients/                  # LLM, embedding clients
│   └── core/                     # Query processing & validation
├── tests/                        # Test suite
├── data/documents/               # PDF files
├── storage/chroma_db/            # Vector database
├── docker/                       # Containerization
├── scripts/                      # Setup scripts
└── requirements.txt
```

**Run Commands:**
```bash
# Dev: python -m uvicorn app.main:app --reload
# Prod: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# Docker: docker-compose up -d
# Tests: pytest tests/ -v
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

#### Option A: Docker (Recommended)

```bash
docker-compose up -d
```

#### Option B: Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

bash scripts/setup_piper.sh

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
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
# Required
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your_groq_key

EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=your_jina_key

# Optional
SESSION_BACKEND=redis  # or 'memory'
REDIS_HOST=redis  # Use 'localhost' for venv setup
```

### Supported Providers

**LLM:**
- `groq` - Free, fast (recommended)
- `openai` - GPT models
- `gemini` - Google Gemini (free)
- `ollama` - Local models

**Embeddings:**
- `jinaai` - Free, good quality (recommended)
- `openai` - text-embedding-3-small
- `ollama` - Local embeddings

See [.env.example](.env.example) for all options.

---

## Voice Features (Optional)

**Docker:** Automatically configured during build.

**Venv:** Run setup script (installs piper + voice model):
```bash
bash scripts/setup_piper.sh
```

### Usage

```bash
# Text to Speech
curl -X POST http://localhost:8000/text-to-speech \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav

# Voice Query
curl -X POST http://localhost:8000/voice-query -F "audio=@question.wav"
```

---

## API Endpoints

### Query
```bash
POST /query
{"question": "your question", "session_id": "optional"}
```

### Documents
```bash
POST /reload     # Reload documents
DELETE /clear    # Clear database
GET /            # Status
```

### Voice
```bash
POST /voice-query           # Speech → Text → Answer
POST /voice-full            # Speech → Text → Answer → Speech
POST /text-to-speech        # Text → Speech
```

### Health
```bash
GET /health                 # Service status and metrics
GET /                       # API info
```

---

## Testing

### Run Tests
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

---

## Troubleshooting

**Port already in use:**
```bash
docker-compose down
# Or change port in docker-compose.yml: "8080:8000"
```

curl -X POST http://localhost:8000/reload
```

**Health check fails:**
```bash
curl http://localhost:8000/health
```

---

## Performance

### Latency Optimizations

- **Streaming responses**: Progressive output reduces time-to-first-token
- **Model caching**: LRU cache for vector searches (100 queries)
- **Async I/O**: Non-blocking operations throughout
- **Rate limiting**: Semaphores prevent resource saturation
- **Optimized models**: faster-whisper (4x faster), int8 quantization

### Scalability

**Horizontal scaling:**
```bash
docker-compose up --scale rag-api=5
```

**Production considerations:**
- Add nginx load balancer
- Use managed Redis (AWS ElastiCache)
- Configure auto-scaling policies
- Monitor with Prometheus/Grafana

---

## Accuracy & Safety

### Hallucination Prevention

- Context-only responses enforced via system prompts
- Out-of-scope query detection and redirection
- Document source tracking in metadata
- Explicit handling of missing information

### Input Validation

- Audio file size limits (10MB)
- Question length constraints
- Empty input detection
- Session validationbash
pip install -r requirements.txt --force-reinstall
```

**Redis connection error:**
```env
# In .env file
SESSION_BACKEND=memory
```

**Voice not working:**
```bash
./setup_piper.sh
# Then download voice models (see Voice Features)
```

**No documents loaded:**
```bash
ls data/documents/
curl -X POST http://localhost:8000/reload
```

---

## License

MIT License
