from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
import json

from documents import load_pdfs
from query import search, stream_response, generate_response
from voice import init_whisper, transcribe, text_to_speech

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

collection = None
sessions = {}

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
    collection = load_pdfs()
    init_whisper()

@app.post("/query")
async def query(q: Query):
    question = validate_query(q.question)
    session_id = q.session_id or "default"
    
    if session_id not in sessions:
        sessions[session_id] = []
    
    context = search(collection, question)
    
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
    audio_bytes = await audio.read()
    question = transcribe(audio_bytes)
    
    q = Query(question=question, session_id=session_id)
    return await query(q)

@app.post("/text-to-speech")
async def tts(q: Query):
    question = validate_query(q.question)
    context = search(collection, question)
    
    answer = generate_response(question, context)
    audio = text_to_speech(answer)
    
    return Response(content=audio, media_type="audio/wav")

@app.get("/health")
async def health():
    return {"status": "ok"}
