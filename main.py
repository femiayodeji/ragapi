from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import command
import document_processor
from config import LLM_MODEL, LLM_PROVIDER, SESSION_BACKEND, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
from stt_service import STTService
from tts_service import TTSService
from session_service import get_session_service
from state import AppState
from utils import initialize_service
import routes
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as aioredis

logging.basicConfig(level=logging.WARNING)
logging.getLogger("__main__").setLevel(logging.INFO)
logger = logging.getLogger(f"RAG App:")

# Track if rate limiting is available
rate_limit_enabled = False


def get_rate_limit_dependencies(times: int, seconds: int):
    """Return rate limit dependency only if Redis is available"""
    if rate_limit_enabled:
        return [Depends(RateLimiter(times=times, seconds=seconds))]
    return []


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rate_limit_enabled
    
    # Initialize fastapi-limiter with Redis (if available)
    try:
        redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}"
        redis_connection = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_connection)
        rate_limit_enabled = True
        logger.info("Rate limiter initialized with Redis")
    except Exception as error:
        rate_limit_enabled = False
        logger.warning(f"Rate limiter disabled (Redis unavailable): {error}")
    
    import chromadb
    chromadb.config.Settings(anonymized_telemetry=False)
    
    try:
        logger.info("Loading ChromaDB...")
        AppState.vectorstore, AppState.rag_chain = command.load_documents()
        count = document_processor.chunk_count(AppState.vectorstore)
        logger.info(f"ChromaDB initiated successfully ({count} chunks)")
    except Exception as error:
        AppState.startup_error = str(error)
        logger.error(f"ChromaDB initialization failed: {error}")
    
    AppState.stt_service = initialize_service(STTService, "Whisper")
    AppState.tts_service = initialize_service(TTSService, "Piper")
    session_backend = "Redis" if SESSION_BACKEND == "redis" else "Memory"
    AppState.session_service = initialize_service(
        lambda: get_session_service(SESSION_BACKEND),
        f"Session ({session_backend})"
    )
    
    yield
    
    # Cleanup
    if rate_limit_enabled:
        try:
            await FastAPILimiter.close()
        except:
            pass


app = FastAPI(title="RAG App", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes - rate limiting applies automatically if Redis is available
app.post("/query", dependencies=get_rate_limit_dependencies(30, 60))(routes.query_endpoint)
app.post("/voice-query", dependencies=get_rate_limit_dependencies(15, 60))(routes.voice_query)
app.post("/voice-full", dependencies=get_rate_limit_dependencies(15, 60))(routes.voice_full)
app.post("/text-to-speech", dependencies=get_rate_limit_dependencies(30, 60))(routes.text_to_speech)

# Session management
app.get("/session/{session_id}/history", dependencies=get_rate_limit_dependencies(30, 60))(routes.session_history)
app.delete("/session/{session_id}", dependencies=get_rate_limit_dependencies(10, 60))(routes.clear_session)

# Admin endpoints
app.post("/reload", dependencies=get_rate_limit_dependencies(5, 60))(routes.reload_documents)
app.delete("/clear", dependencies=get_rate_limit_dependencies(2, 60))(routes.clear_database)


@app.get("/", dependencies=get_rate_limit_dependencies(60, 60))
async def root():
    pdf_files = document_processor.get_pdf_files()
    chunk_count = document_processor.chunk_count(AppState.vectorstore)
    
    return {
        "status": "running",
        "services": {
            "documents": AppState.vectorstore is not None,
            "session": AppState.session_service is not None,
            "stt": AppState.stt_service is not None,
            "tts": AppState.tts_service is not None
        },
        "documents": {
            "pdf_count": len(pdf_files),
            "chunk_count": chunk_count
        },
        "llm": f"{LLM_PROVIDER}/{LLM_MODEL}",
        "rate_limiting": rate_limit_enabled
    }


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_HOST, SERVER_PORT
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
