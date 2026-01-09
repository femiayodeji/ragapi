from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import uuid
import logging
from config import PDF_DIR, SESSION_MAX_HISTORY
import query as query_module

logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE_MB = 10
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024


def initialize_service(service_factory, service_name: str):
    try:
        logger.info(f"Loading {service_name}...")
        service = service_factory()
        logger.info(f"{service_name} initiated successfully")
        return service
    except Exception as error:
        logger.warning(f"{service_name} initialization failed: {error}")
        return None


def ensure_documents_loaded(app_state):
    if app_state.startup_error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service initialization failed: {app_state.startup_error}"
        )
    if not app_state.rag_chain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No documents loaded. Add PDFs to '{PDF_DIR}' and restart or call /reload"
        )


def ensure_service_available(service, service_name: str):
    if not service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} service unavailable"
        )


def validate_audio_data(audio_bytes: bytes):
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file"
        )
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file too large (max {MAX_AUDIO_SIZE_MB}MB)"
        )


def transcribe_audio(stt_service, audio_bytes: bytes) -> str:
    transcription = stt_service.transcribe(audio_bytes)
    if not transcription["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription failed: {transcription.get('error', 'Unknown error')}"
        )
    
    question = transcription["text"]
    if not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No speech detected in audio"
        )
    return question


def get_or_create_session_id(provided_id: Optional[str]) -> str:
    return provided_id or str(uuid.uuid4())


def get_session_context(session_service, session_id: str) -> Optional[str]:
    if not session_service:
        return None
    
    try:
        if session_service.session_exists(session_id):
            return session_service.format_history(session_id, SESSION_MAX_HISTORY)
    except Exception as error:
        logger.warning(f"Session context retrieval failed: {error}")
    return None


def save_session_message(session_service, session_id: str, role: str, content: str):
    if not session_service:
        return
    
    try:
        session_service.add_message(session_id, role, content)
    except Exception as error:
        logger.warning(f"Failed to save {role} message: {error}")


def process_query_with_session(rag_chain, session_service, question: str, session_id: str) -> Dict[str, Any]:
    session_context = get_session_context(session_service, session_id)
    save_session_message(session_service, session_id, "user", question)
    
    answer = query_module.query_documents(rag_chain, question, session_context)
    
    save_session_message(session_service, session_id, "assistant", answer)
    
    return {"question": question, "answer": answer, "session_id": session_id}


def process_query_with_session_stream(rag_chain, session_service, question: str, session_id: str):
    session_context = get_session_context(session_service, session_id)
    save_session_message(session_service, session_id, "user", question)
    
    full_answer = ""
    for chunk in query_module.query_documents_stream(rag_chain, question, session_context):
        full_answer += chunk
        yield chunk
    
    save_session_message(session_service, session_id, "assistant", full_answer)
