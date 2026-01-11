from fastapi import HTTPException, UploadFile, File, status
from fastapi.responses import StreamingResponse
from typing import Optional
from starlette.concurrency import run_in_threadpool
import io
import json
import uuid
import logging
import tempfile

from app.models import Query
from app.core import query as query_module

logger = logging.getLogger(__name__)

MAX_AUDIO_SIZE_MB = 10
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024


def validate_audio(audio_bytes: bytes):
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file")
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file too large (max {MAX_AUDIO_SIZE_MB}MB)"
        )


def transcribe_audio(stt_service, audio_bytes: bytes) -> str:
    result = stt_service.transcribe(audio_bytes)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription failed: {result.get('error', 'Unknown error')}"
        )
    
    text = result["text"]
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No speech detected")
    
    return text


async def query_endpoint(query: Query, app):
    if app.startup_error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=app.startup_error)
    if not app.rag_chain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents loaded")
    
    session_id = query.session_id or str(uuid.uuid4())
    
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
            yield f"data: {json.dumps({'type': 'question', 'question': query.question})}\n\n"
            
            for chunk in query_module.query_with_session_stream(
                app.rag_chain, app.session_service, query.question, session_id
            ):
                yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


async def voice_query(audio: UploadFile, session_id: Optional[str], app):
    if not app.rag_chain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents loaded")
    if not app.stt_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="STT unavailable")
    
    audio_bytes = await audio.read()
    validate_audio(audio_bytes)
    
    async with app.stt_semaphore:
        question = await run_in_threadpool(transcribe_audio, app.stt_service, audio_bytes)
    
    session_id = session_id or str(uuid.uuid4())
    
    async def event_generator():
        yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
        yield f"data: {json.dumps({'type': 'question', 'question': question})}\n\n"
        
        for chunk in query_module.query_with_session_stream(
            app.rag_chain, app.session_service, question, session_id
        ):
            yield f"data: {json.dumps({'type': 'token', 'token': chunk})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def voice_full(audio: UploadFile, session_id: Optional[str], app):
    if not app.rag_chain:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents loaded")
    if not app.stt_service or not app.tts_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="STT or TTS unavailable")
    
    audio_bytes = await audio.read()
    validate_audio(audio_bytes)
    
    async with app.stt_semaphore:
        question = await run_in_threadpool(transcribe_audio, app.stt_service, audio_bytes)
    
    session_id = session_id or str(uuid.uuid4())
    result = query_module.query_with_session(app.rag_chain, app.session_service, question, session_id)
    answer = result["answer"]
    
    async with app.tts_semaphore:
        tts_result = await run_in_threadpool(app.tts_service.synthesize, answer)
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


async def text_to_speech(query: Query, app):
    if not app.tts_service:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="TTS unavailable")
    
    async with app.tts_semaphore:
        result = await run_in_threadpool(app.tts_service.synthesize, query.question)
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS failed: {result.get('error')}"
        )
    
    return StreamingResponse(io.BytesIO(result["audio_bytes"]), media_type="audio/wav")


async def reload_documents(app):
    from app.services import document_processor
    
    logger.info("Reloading documents...")
    app.vectorstore, app.rag_chain, count = document_processor.reload_documents()
    app.startup_error = None
    logger.info(f"Documents reloaded ({count} chunks)")
    return {"message": "Documents reloaded", "chunk_count": count}


async def clear_database(app):
    from app.services import document_processor
    
    logger.info("Clearing database...")
    document_processor.clear_all()
    app.vectorstore = None
    app.rag_chain = None
    logger.info("Database cleared")
    return {"message": "Database cleared. Add documents and restart or call /reload"}
