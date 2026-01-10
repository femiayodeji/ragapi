# RAG Application

Multi-provider RAG (Retrieval-Augmented Generation) with voice support and session management.

## Quick Start

```bash
# 1. Get API keys (free): https://console.groq.com/keys & https://jina.ai/embeddings
cp .env.example .env
nano .env  # Add your keys

# 2. Run with Docker (recommended)
docker-compose up -d

# OR run with venv
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 main.py

# 3. Test
curl http://localhost:8000/
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "What documents do I need?", "session_id": "demo"}'
```

**Note:** Sample PDF in `documents/` is auto-ingested on startup. Add more PDFs → restart or call `/reload`.

---

## Setup

### Docker
```bash
cat > .env << 'EOF'
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your_key_here
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=your_key_here
SESSION_BACKEND=redis
REDIS_HOST=redis
EOF

mkdir -p documents && cp your-files/*.pdf documents/
docker-compose up -d
```

### Virtual Environment
```bash
python3 -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip && pip install -r requirements.txt
cp .env.example .env && nano .env  # Add keys, set SESSION_BACKEND=memory
mkdir -p documents && cp your-files/*.pdf documents/
python3 main.py
```

**Optional Redis:** `sudo apt install redis-server` or `docker run -d -p 6379:6379 redis:alpine`

---

## Voice Features (Optional)

```bash
mkdir -p voices && cd voices
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..
```

---

## API Endpoints

```bash
# Query
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "...", "session_id": "user123"}'

# Documents
curl -X POST http://localhost:8000/reload  # Reload
curl -X DELETE http://localhost:8000/clear  # Clear DB

# Session
curl http://localhost:8000/session/user123/history
curl -X DELETE http://localhost:8000/session/user123

# Voice
curl -X POST http://localhost:8000/voice-query -F "audio=@file.wav"
curl -X POST http://localhost:8000/text-to-speech -H "Content-Type: application/json" -d '{"text": "Hello"}' --output speech.wav
```

**Docs:** http://localhost:8000/docs

---

## Configuration

### LLM Providers
```env
# Groq (free) - https://console.groq.com/keys
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_...

# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=sk-...

# Gemini (free) - https://ai.google.dev/
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
LLM_API_KEY=...

# Ollama (local)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
LLM_BASE_URL=http://localhost:11434
```

### Embedding Providers
```env
# Jina AI (free) - https://jina.ai/embeddings
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=jina_...

# OpenAI
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-...

# Ollama (local)
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

See [.env.example](.env.example) for all options.

---

## Document Management

```bash
# Add & reload
cp file.pdf documents/ && curl -X POST http://localhost:8000/reload

# Verify
curl http://localhost:8000/  # Check "pdf_count" and "chunk_count"

# Clear & rebuild
curl -X DELETE http://localhost:8000/clear && curl -X POST http://localhost:8000/reload
```

PDFs in `documents/` are auto-processed on startup (~1-2s per PDF). Only new/modified files processed.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| httpx error | `pip install httpx==0.24.1 --force-reinstall` |
| Dependencies | `pip install -r requirements.txt --force-reinstall` |
| Container logs | `docker-compose logs rag-app` |
| Port in use | Change to `"8080:8000"` in docker-compose.yml |
| No documents | `ls documents/` then `/reload` endpoint |
| Redis error | Set `SESSION_BACKEND=memory` in .env |
| Voice issues | Download models (see Voice Features) |

---

## License

MIT License
