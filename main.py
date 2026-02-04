from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
import json
import signal
import sys
import asyncio
from functools import partial

from documents import load_pdfs
from query import search, stream_response
from voice import transcribe, text_to_speech

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

collection = None
sessions = {}

def cleanup_handler(signum, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

class Query(BaseModel):
    question: str
    session_id: Optional[str] = None

def validate_query(question: str) -> str:
    question = question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if len(question) > 1000:
        raise HTTPException(status_code=400, detail="Question too long (max 1000 characters)")
    return question

@app.on_event("startup")
async def startup():
    global collection
    loop = asyncio.get_event_loop()
    collection = await loop.run_in_executor(None, load_pdfs)

@app.post("/query")
async def query(q: Query):
    question = validate_query(q.question)
    session_id = q.session_id or "default"
    
    if session_id not in sessions:
        sessions[session_id] = []
    
    loop = asyncio.get_event_loop()
    context = await loop.run_in_executor(None, search, collection, question)
    
    async def stream():
        full_response = ""
        for token in stream_response(question, context, sessions[session_id]):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"
        
        sessions[session_id].append({"role": "user", "content": question})
        sessions[session_id].append({"role": "assistant", "content": full_response})
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(stream(), media_type="text/event-stream")

@app.post("/voice-query")
async def voice_query(audio: UploadFile = File(...), session_id: Optional[str] = None):
    loop = asyncio.get_event_loop()
    audio_bytes = await audio.read()
    question = await loop.run_in_executor(None, transcribe, audio_bytes)
    
    q = Query(question=question, session_id=session_id)
    return await query(q)

@app.post("/text-to-speech")
async def tts(q: Query):
    loop = asyncio.get_event_loop()
    audio = await loop.run_in_executor(None, text_to_speech, q.question)
    
    return Response(content=audio, media_type="audio/mpeg")

@app.get("/health")
async def health():
    return {"status": "ok"}
