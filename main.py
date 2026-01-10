from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import logging
import asyncio
import chromadb
import document_processor
from config import LLM_MODEL, LLM_PROVIDER, SESSION_BACKEND
from stt_service import STTService
from tts_service import TTSService
from session_service import get_session_service
from models import Query
import routes

logging.basicConfig(level=logging.WARNING)
logging.getLogger("__main__").setLevel(logging.INFO)
logger = logging.getLogger("RAG App")


class AppState:
    vectorstore = None
    rag_chain = None
    stt_service = None
    tts_service = None
    session_service = None
    startup_error = None
    stt_semaphore = None
    tts_semaphore = None


def init_service(factory, name: str):
    try:
        logger.info(f"Loading {name}...")
        service = factory()
        logger.info(f"{name} ready")
        return service
    except Exception as e:
        logger.warning(f"{name} failed: {e}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    chromadb.config.Settings(anonymized_telemetry=False)
    
    try:
        logger.info("Loading ChromaDB...")
        AppState.vectorstore, AppState.rag_chain = document_processor.load_documents()
        count = document_processor.chunk_count(AppState.vectorstore)
        logger.info(f"ChromaDB ready ({count} chunks)")
    except Exception as e:
        AppState.startup_error = str(e)
        logger.error(f"ChromaDB failed: {e}")
    
    AppState.stt_service = init_service(STTService, "Whisper")
    AppState.tts_service = init_service(TTSService, "Piper")
    
    backend = "Redis" if SESSION_BACKEND == "redis" else "Memory"
    AppState.session_service = init_service(
        lambda: get_session_service(SESSION_BACKEND),
        f"Sessions ({backend})"
    )
    
    AppState.stt_semaphore = asyncio.Semaphore(4)
    AppState.tts_semaphore = asyncio.Semaphore(4)
    
    yield


app = FastAPI(title="RAG App", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/query")
async def query_route(query: Query):
    return await routes.query_endpoint(query, AppState)


@app.post("/voice-query")
async def voice_query_route(audio: UploadFile = File(...), session_id: Optional[str] = None):
    return await routes.voice_query(audio, session_id, AppState)


@app.post("/voice-full")
async def voice_full_route(audio: UploadFile = File(...), session_id: Optional[str] = None):
    return await routes.voice_full(audio, session_id, AppState)


@app.post("/text-to-speech")
async def tts_route(query: Query):
    return await routes.text_to_speech(query, AppState)


@app.get("/session/{session_id}/history")
async def session_history_route(session_id: str):
    return await routes.session_history(session_id, AppState)


@app.delete("/session/{session_id}")
async def clear_session_route(session_id: str):
    return await routes.clear_session(session_id, AppState)


@app.post("/reload")
async def reload_route():
    return await routes.reload_documents(AppState)


@app.delete("/clear")
async def clear_route():
    return await routes.clear_database(AppState)


@app.get("/")
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
        "llm": f"{LLM_PROVIDER}/{LLM_MODEL}"
    }


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_HOST, SERVER_PORT
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
