from fastapi import HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import json
import logging
from state import AppState
from models import Query
from utils import (
    ensure_documents_loaded, ensure_service_available,
    validate_audio_data, transcribe_audio, get_or_create_session_id,
    process_query_with_session, process_query_with_session_stream
)
import command

logger = logging.getLogger(__name__)


async def query_endpoint(query: Query):
    ensure_documents_loaded(AppState)
    session_id = get_or_create_session_id(query.session_id)
    
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
            yield f"data: {json.dumps({'type': 'question', 'question': query.question})}\n\n"
            
            for chunk in process_query_with_session_stream(AppState.rag_chain, AppState.session_service, query.question, session_id):
                yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


async def voice_query(audio: UploadFile = File(...), session_id: Optional[str] = None):
    ensure_documents_loaded(AppState)
    ensure_service_available(AppState.stt_service, "Speech-to-text")
    
    audio_bytes = await audio.read()
    validate_audio_data(audio_bytes)
    question = transcribe_audio(AppState.stt_service, audio_bytes)
    
    session_id = get_or_create_session_id(session_id)
    
    async def event_generator():
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
        yield f"data: {json.dumps({'type': 'question', 'question': question})}\n\n"
        
        for chunk in process_query_with_session_stream(AppState.rag_chain, AppState.session_service, question, session_id):
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def voice_full(audio: UploadFile = File(...), session_id: Optional[str] = None):
    ensure_documents_loaded(AppState)
    ensure_service_available(AppState.stt_service, "Speech-to-text")
    ensure_service_available(AppState.tts_service, "Text-to-speech")
    
    audio_bytes = await audio.read()
    validate_audio_data(audio_bytes)
    question = transcribe_audio(AppState.stt_service, audio_bytes)
    
    session_id = get_or_create_session_id(session_id)
    result = process_query_with_session(AppState.rag_chain, AppState.session_service, question, session_id)
    answer = result["answer"]
    
    tts_result = AppState.tts_service.synthesize(answer)
    if not tts_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS failed: {tts_result.get('error')}"
        )
    
    return StreamingResponse(
        io.BytesIO(tts_result["audio_bytes"]),
        media_type="audio/wav",
        headers={"X-Session-Id": session_id}
    )


async def text_to_speech(query: Query):
    ensure_service_available(AppState.tts_service, "Text-to-speech")
    
    result = AppState.tts_service.synthesize(query.question)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech failed: {result.get('error', 'Unknown error')}"
        )
    
    return StreamingResponse(io.BytesIO(result["audio_bytes"]), media_type="audio/wav")


async def session_history(session_id: str):
    """Get conversation history for a session."""
    ensure_service_available(AppState.session_service, "Session service")
    
    if not AppState.session_service.session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    messages = AppState.session_service.get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(messages),
        "messages": [msg.to_dict() for msg in messages]
    }


async def clear_session(session_id: str):
    """Clear conversation history for a session."""
    ensure_service_available(AppState.session_service, "Session service")
    
    if not AppState.session_service.session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    AppState.session_service.clear_session(session_id)
    return {"message": "Session cleared successfully", "session_id": session_id}


async def reload_documents():
    """Reload documents from the documents folder."""
    logger.info("Reloading documents...")
    AppState.vectorstore, AppState.rag_chain, count = command.reload_documents(AppState.vectorstore)
    AppState.startup_error = None
    logger.info(f"Documents reloaded successfully ({count} chunks)")
    return {"message": "Documents reloaded", "chunk_count": count}


async def clear_database():
    """Clear all documents and vector store."""
    import document_processor
    logger.info("Clearing database...")
    document_processor.clear_all()
    AppState.vectorstore = None
    AppState.rag_chain = None
    logger.info("Database cleared successfully")
    return {"message": "Database cleared. Add documents and restart or call /reload"}
