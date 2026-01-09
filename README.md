# RAG Application

Multi-provider RAG (Retrieval-Augmented Generation) with voice support and session management.

## Features

- PDF document processing with ChromaDB vector store
- Multi-provider LLM support (Groq, OpenAI, Gemini, Anthropic, Ollama)
- Multi-provider embeddings (Jina AI, OpenAI, Gemini, Ollama)
- Speech-to-Text using Whisper
- Text-to-Speech using Piper
- Session management with Redis or in-memory storage
- REST API with FastAPI
- Docker support with Docker Compose

## Quick Setup

### 1. Clone & Setup Environment

```bash
# Clone repository
cd ragapp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example configuration and edit with your API keys:

```bash
cp .env.example .env
# Edit .env with your preferred editor
```

**Minimal configuration** (.env):

```env
# Required: Choose your LLM provider
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your_groq_api_key

# Required: Choose your embedding provider
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=your_jina_api_key
```

**Free API Keys:**
- Groq (fast, free tier): https://console.groq.com/keys
- Jina AI (free embeddings): https://jina.ai/embeddings
- Gemini (free tier): https://ai.google.dev/

### 3. Add Documents and Run

```bash
# Place your PDF files in the documents/ folder
mkdir -p documents
cp your-document.pdf documents/

# Start the application
python main.py
```

Access at **http://localhost:8000**

### Optional: Redis for Session Management

The application works with or without Redis. Without Redis, sessions are stored in memory.

```bash
# Install Redis locally
sudo apt install redis-server  # Ubuntu/Debian
brew install redis             # macOS

# Or use Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

### Optional: Voice Features Setup

Voice features require additional dependencies:

**Text-to-Speech (Piper):**
```bash
# The application includes a Piper voice model in voices/
# Model: en_US-lessac-medium.onnx (already included)
# Install Piper: https://github.com/rhasspy/piper

# Verify voice files exist
ls voices/
# Should show: en_US-lessac-medium.onnx, en_US-lessac-medium.onnx.json
```

**Speech-to-Text (Whisper):**
```bash
# Whisper base model is automatically downloaded on first use
# Requires: pip install openai-whisper (already in requirements.txt)
```

**Note:** Voice endpoints work even if Piper is not installed - they return appropriate errors.

## Docker Deployment

```bash
# Start all services (Redis, Ollama, RAG app)
docker-compose up -d

# View logs
docker-compose logs -f rag-app

# Stop services
docker-compose down
```

## API Endpoints

### Core RAG

- **POST /query** - Text query with session support
  ```bash
  curl -X POST http://localhost:8000/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What is the main topic?", "session_id": "user123"}'
  ```

### Voice Features

- **POST /voice-query** - Voice input → text response
- **POST /voice-full** - Voice input → voice response
- **POST /text-to-speech** - Convert text to speech

### Document Management

- **POST /reload** - Reload documents from documents/ folder
- **DELETE /clear** - Clear vector database (requires rebuild)

### Session Management

- **GET /session/{id}/history** - Get conversation history
- **DELETE /session/{id}** - Clear session

### Status

- **GET /** - Health check & system status

## Configuration Options

All configuration is done via `.env` file. See [.env.example](.env.example) for full options.

### LLM Providers

```env
# Groq (Recommended - Fast & Free)
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_xxxxx

# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=sk-xxxxx

# Gemini
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
LLM_API_KEY=xxxxx

# Ollama (Local, no API key needed)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
LLM_BASE_URL=http://localhost:11434
```

### Embedding Providers

```env
# Jina AI (Recommended - Free)
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=jina_xxxxx

# OpenAI
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-xxxxx

# Ollama (Local)
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
LLM_BASE_URL=http://localhost:11434
```

### Document Processing

```env
CHUNK_SIZE=1000          # Characters per chunk
CHUNK_OVERLAP=200        # Overlap between chunks
TOP_K=3                  # Number of relevant chunks to retrieve
```

### Session & Performance

```env
SESSION_BACKEND=redis    # or "memory"
SESSION_EXPIRE=3600      # Session timeout in seconds
SESSION_MAX_HISTORY=10   # Max messages per session
```

## Project Structure

### Core Application
```
main.py                  - FastAPI application & startup
routes.py                - API endpoint definitions
state.py                 - Application state management
config.py                - Configuration loader
```

### Document Processing & RAG
```
document_processor.py    - PDF processing & vector store operations
embedding_client.py      - Multi-provider embedding client
llm_client.py           - Multi-provider LLM client
query.py                - RAG chain & query logic
command.py              - Document loading orchestration
```

### Services
```
session_service.py      - Session management (Redis/Memory)
stt_service.py          - Speech-to-Text (Whisper)
tts_service.py          - Text-to-Speech (Piper)
```

### Data & Storage
```
documents/              - PDF files to process
chroma_db/              - ChromaDB vector store
processed_files.txt     - Tracking processed documents
```

## Maintenance Guide

### Adding New Documents

1. Copy PDFs to `documents/` folder
2. Restart application or call `/reload` endpoint
3. Only new/modified documents are processed

### Changing Embedding Model

**Important:** Changing embedding models requires rebuilding the vector store.

```bash
# 1. Clear existing database
curl -X DELETE http://localhost:8000/clear

# 2. Update .env with new embedding model
# 3. Restart application
python main.py
```

### Common Tasks

**Check status:**
```bash
curl http://localhost:8000/
```

**Reload documents:**
```bash
curl -X POST http://localhost:8000/reload
```

**View session history:**
```bash
curl http://localhost:8000/session/{session_id}/history
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Documents not loading | Check PDFs are in `documents/` folder and valid |
| API key errors | Verify keys in `.env` file, no extra spaces |
| Redis connection issues | App works without Redis (uses memory sessions)<br>Install: `sudo apt install redis-server` or Docker |
| Voice features not working | Piper TTS is optional - see Voice Features Setup<br>Whisper auto-downloads on first use |
| Out of memory | Reduce `CHUNK_SIZE`, `TOP_K` in `.env`<br>Use lighter models (gemini-1.5-flash) |

## Development

### Code Structure

The application follows a modular design:
- **Services** are initialized in `main.py` lifespan
- **State** is managed in `state.py` (AppState)
- **Routes** are defined in `routes.py`
- **Configuration** is centralized in `config.py`

### Adding New Provider

**LLM Provider** - Update `llm_client.py`
**Embedding Provider** - Update `embedding_client.py`

See inline code comments for implementation patterns.

## License

MIT