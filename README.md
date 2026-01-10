# RAG Application

Multi-provider RAG API with voice support and session management.

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
nano .env  # Add your API keys
```

### 3. Choose Your Setup

#### Option A: Docker (Recommended)

```bash
mkdir -p documents
cp your-files/*.pdf documents/
docker-compose up -d
```

#### Option B: Virtual Environment

```bash
# Create and activate venv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Add new PDF
mkdir -p documents
cp your-files/*.pdf documents/

# Setup voice support (optional)
./setup_piper.sh

# Run
python3 main.py
```

### 4. Test

```bash
curl http://localhost:8000/
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "demo"}'
```

**API Docs:** http://localhost:8000/docs

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
./setup_piper.sh
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

### Sessions
```bash
GET /session/{id}/history    # View history
DELETE /session/{id}         # Clear session
```

### Voice
```bash
POST /voice-query           # Speech → Text → Answer
POST /voice-full            # Speech → Text → Answer → Speech
POST /text-to-speech        # Text → Speech
```

---

## Troubleshooting

**Port already in use:**
```bash
docker-compose down
# Or change port in docker-compose.yml: "8080:8000"
```

**Dependencies error:**
```bash
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
ls documents/  # Check files exist
curl -X POST http://localhost:8000/reload
```

---

## License

MIT License
