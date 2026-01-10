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

## Prerequisites

- **Python 3.11+** (for local/venv setup)
- **Docker & Docker Compose** (for Docker setup)
- **Redis** (optional - for persistent sessions)
- **API Keys** for your chosen LLM and embedding providers

## Table of Contents

- [Quick Start](#quick-start-5-minutes)
- [Docker Setup](#docker-setup-recommended)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Voice Features Setup](#voice-features-setup-optional)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration-options)
- [Troubleshooting](#troubleshooting)
- [Quick Reference](#quick-reference)

---

## Quick Start (5 Minutes)

Get up and running with the example document already included:

### Using Docker (Easiest)

```bash
# 1. Configure API keys
cp .env.example .env
nano .env  # Add your Groq and Jina AI keys (see links below)

# 2. Start everything
docker-compose up -d

# 3. Test it (after ~10 seconds)
curl http://localhost:8000/
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What documents do I need?", "session_id": "demo"}'
```

### Using Virtual Environment

```bash
# 1. Setup environment
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
nano .env  # Add your Groq and Jina AI keys

# 3. Run the application
python3 main.py

# 4. Test it (in another terminal)
curl http://localhost:8000/
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What documents do I need?", "session_id": "demo"}'
```

**Free API Keys:**
- Groq (LLM): https://console.groq.com/keys
- Jina AI (Embeddings): https://jina.ai/embeddings

**Note:** The repository includes a sample PDF in `documents/` folder that is automatically ingested on startup. To add your own documents, simply place PDF files in the `documents/` folder and restart the application or call the `/reload` endpoint.

---

## Docker Setup (Recommended)

Docker setup includes Redis and all dependencies pre-configured.

#### Step 1: Configure Environment

```bash
# Create .env file with your configuration
cat > .env << 'EOF'
# LLM Provider Configuration
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your_groq_api_key_here

# Embedding Provider Configuration
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=your_jina_api_key_here

# Session Configuration
SESSION_BACKEND=redis
REDIS_HOST=redis
REDIS_PORT=6379
EOF
```

#### Step 2: Add Your Documents

```bash
# Create documents folder and add your PDF files
mkdir -p documents
cp /path/to/your/documents/*.pdf documents/
```

#### Step 3: Start Services

```bash
# Build and start all services (Redis + RAG app)
docker-compose up -d

# View logs to verify startup
docker-compose logs -f rag-app

# Wait for "RAG app ready" message
```

#### Step 4: Test the Application

```bash
# Health check
curl http://localhost:8000/

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "test123"}'
```

#### Docker Management Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f rag-app

# Rebuild after code changes
docker-compose up -d --build

# Clean up completely
docker-compose down -v
```

---

## Virtual Environment Setup

#### Step 1: Clone & Create Virtual Environment

```bash
# Navigate to project directory
cd /path/to/ragapi

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

#### Step 2: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Note:** If you encounter dependency conflicts, ensure you're using Python 3.11+.

#### Step 3: Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
# LLM Provider Configuration
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=your_groq_api_key_here

# Embedding Provider Configuration
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=your_jina_api_key_here

# Session Configuration (use memory if Redis not available)
SESSION_BACKEND=memory
EOF
```

#### Step 4: Optional - Install Redis

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Or use Docker
docker run -d --name redis -p 6379:6379 redis:alpine

# Then update .env:
SESSION_BACKEND=redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

#### Step 5: Add Documents

```bash
# Create documents folder
mkdir -p documents

# Add your PDF files
cp /path/to/your/documents/*.pdf documents/
```

#### Step 6: Start the Application

```bash
# Run the application
python3 main.py

# Or use uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 7: Test the Application

```bash
# In a new terminal
curl http://localhost:8000/

# Test query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?", "session_id": "test123"}'
```

---

## Voice Features Setup (Optional)

Voice features work even if components are not installed - endpoints return appropriate errors.

### Text-to-Speech (Piper)

Download the Piper voice model:

```bash
# Create voices directory
mkdir -p voices
cd voices

# Download voice model and config
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

# Verify files
ls -lh
# Should show: en_US-lessac-medium.onnx (~63M), en_US-lessac-medium.onnx.json

# Return to project directory
cd ..
```

**Note:** For Docker deployments, voice files in `voices/` folder are automatically mounted to the container.

For additional voices, visit: https://github.com/rhasspy/piper

### Speech-to-Text (Whisper)

Whisper base model is automatically downloaded on first use:
```bash
# Models are downloaded to ~/.cache/whisper/
# Requires: faster-whisper (already in requirements.txt)
# No manual setup needed
```

---

## Troubleshooting

### Dependency Issues

**httpx compatibility error:**
```bash
# Ensure httpx is pinned to compatible version
pip install httpx==0.24.1 --force-reinstall
```

**LangChain version conflicts:**
```bash
# Reinstall with exact versions from requirements.txt
pip install -r requirements.txt --force-reinstall
```

### Docker Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs rag-app

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Port already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8080:8000"  # Use 8080 instead
```

### Application Issues

**No documents loaded:**
```bash
# Ensure PDFs are in documents/ folder
ls -la documents/

# Trigger reload
curl -X POST http://localhost:8000/reload
```

**Redis connection failed:**
```bash
# Switch to memory backend in .env
SESSION_BACKEND=memory

# Or check Redis is running
redis-cli ping  # Should return PONG
```

**Voice features not working:**
```bash
# Download Piper voice models
mkdir -p voices
cd voices
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..

# Verify files exist
ls -lh voices/
```

**Import errors or module not found:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **Issues**: Check application logs for detailed error messages
- **Configuration**: See [.env.example](.env.example) for all options

## License

See LICENSE file for details.

---

## API Endpoints

### Document Query

**POST /query** - Query documents with streaming response
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What documents do I need for passport renewal?",
    "session_id": "user123"
  }'
```

### Voice Features

**POST /voice-query** - Voice input → text response (streaming)
```bash
curl -X POST http://localhost:8000/voice-query \
  -F "audio=@recording.wav" \
  -F "session_id=user123"
```

**POST /voice-full** - Voice input → voice response
```bash
curl -X POST http://localhost:8000/voice-full \
  -F "audio=@recording.wav" \
  -F "session_id=user123" \
  --output response.wav
```

**POST /text-to-speech** - Convert text to speech
```bash
curl -X POST http://localhost:8000/text-to-speech \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how can I help you?"}' \
  --output speech.wav
```

### Document Management

**POST /reload** - Reload documents from documents/ folder
```bash
curl -X POST http://localhost:8000/reload
```

**DELETE /clear** - Clear vector database (requires reload after)
```bash
curl -X DELETE http://localhost:8000/clear
```

### Session Management

**GET /session/{session_id}/history** - Get conversation history
```bash
curl http://localhost:8000/session/user123/history
```

**DELETE /session/{session_id}** - Clear session
```bash
curl -X DELETE http://localhost:8000/session/user123
```

### System Status

**GET /** - Health check & system status
```bash
curl http://localhost:8000/
```

**Interactive API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Configuration Options

### LLM Providers

Configure in `.env` file:

**Groq (Recommended - Fast & Free)**
```env
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_API_KEY=gsk_your_key_here
```
Get free key: https://console.groq.com/keys

**OpenAI (Paid)**
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_API_KEY=sk-your_key_here
```

**Google Gemini (Free Tier)**
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
LLM_API_KEY=your_key_here
```
Get free key: https://ai.google.dev/

**Anthropic Claude (Paid)**
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
LLM_API_KEY=sk-ant-your_key_here
```

**Ollama (Local - No API Key)**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
LLM_BASE_URL=http://localhost:11434
```

### Embedding Providers

**Jina AI (Recommended - Free)**
```env
EMBEDDING_PROVIDER=jinaai
EMBEDDING_MODEL=jina-embeddings-v3
EMBEDDING_API_KEY=jina_your_key_here
```
Get free key: https://jina.ai/embeddings

**OpenAI Embeddings (Paid)**
```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-your_key_here
```

**Google Gemini Embeddings**
```env
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=text-embedding-004
EMBEDDING_API_KEY=your_key_here
```

**Ollama (Local)**
```env
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
```

### Additional Settings

See [.env.example](.env.example) for complete configuration options including:
- Document processing (chunk size, overlap, top-k results)
- Session management (backend, expiration, history limit)
- Server settings (host, port)
- Voice features (Whisper model, voice directory)

---

## Getting Free API Keys

### Groq (Recommended - Fast & Free LLM)
1. Visit: https://console.groq.com/keys
2. Sign up for a free account
3. Generate an API key
4. Use in `.env`:
   ```env
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.3-70b-versatile
   LLM_API_KEY=gsk_your_key_here
   ```

### Jina AI (Free Embeddings)
1. Visit: https://jina.ai/embeddings
2. Sign up for a free account
3. Get your API key
4. Use in `.env`:
   ```env
   EMBEDDING_PROVIDER=jinaai
   EMBEDDING_MODEL=jina-embeddings-v3
   EMBEDDING_API_KEY=jina_your_key_here
   ```

### Google Gemini (Free Tier)
1. Visit: https://ai.google.dev/
2. Get API key from Google AI Studio
3. Use in `.env`:
   ```env
   LLM_PROVIDER=gemini
   LLM_MODEL=gemini-1.5-flash
   LLM_API_KEY=your_key_here
   ```

---

## Quick Reference

### Document Ingestion

The application automatically ingests PDF documents from the `documents/` folder on startup.

**Adding New Documents:**

```bash
# Method 1: Add files and restart
cp your-document.pdf documents/
python3 main.py  # or docker-compose restart rag-app

# Method 2: Hot reload without restart
cp your-document.pdf documents/
curl -X POST http://localhost:8000/reload
```

**How It Works:**
- Documents are automatically processed into chunks
- Embeddings are generated and stored in ChromaDB
- Only new or modified files are processed (tracked in `processed_files.txt`)
- Typical processing time: ~1-2 seconds per PDF

**Verify Documents Loaded:**
```bash
# Check status endpoint
curl http://localhost:8000/
# Look for: "pdf_count": X, "chunk_count": Y
```

**Clear and Rebuild Database:**
```bash
# If you need to reprocess all documents
curl -X DELETE http://localhost:8000/clear
# Then restart or call /reload
```

### Common Commands

```bash
# Start application (venv)
python3 main.py

# Start with Docker
docker-compose up -d

# View Docker logs
docker-compose logs -f rag-app

# Stop Docker services
docker-compose down

# Rebuild Docker after code changes
docker-compose up -d --build

# Health check
curl http://localhost:8000/

# Query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this about?", "session_id": "test"}'

# Add new document and reload
cp new-doc.pdf documents/
curl -X POST http://localhost:8000/reload

# Check Python environment
which python3
pip list | grep -E "langchain|chromadb|httpx"
```

### File Structure

```
ragapi/
├── documents/              # 📁 Place your PDF files here
│   └── *.pdf              # Automatically ingested on startup
├── voices/                 # 🔊 Piper TTS voice models
├── chroma_db/              # 💾 ChromaDB vector store (auto-generated)
├── .env                    # ⚙️ Your configuration (copy from .env.example)
├── processed_files.txt     # 📝 Tracks processed documents
├── main.py                 # 🚀 Application entry point
├── requirements.txt        # 📦 Python dependencies
├── Dockerfile              # 🐳 Docker image definition
├── docker-compose.yml      # 🐳 Docker services configuration
└── README.md               # 📖 This file
```

---

- **Configuration**: See [.env.example](.env.example) for all options

## License

MIT License - See LICENSE file for details.
