import os
import time
from typing import List
from pypdf import PdfReader
from chromadb import Client
from chromadb.config import Settings
import chromadb

from config import PDF_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from query import get_embeddings

chromadb.api.client.SharedSystemClient.clear_system_cache()

def chunk_text(text: str) -> List[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return chunks

def load_pdfs():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    
    chroma_client = Client(Settings(
        persist_directory=CHROMA_DIR,
        anonymized_telemetry=False,
        allow_reset=True
    ))
    collection = chroma_client.get_or_create_collection("documents")
    
    existing_count = collection.count()
    if existing_count > 0:
        return collection
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        return collection
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        reader = PdfReader(pdf_path)
        text = " ".join([page.extract_text() for page in reader.pages])
        chunks = chunk_text(text)
        
        batch_size = 20
        all_embeddings = []
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            embeddings = get_embeddings(batch)
            all_embeddings.extend(embeddings)
            if i + batch_size < len(chunks):
                time.sleep(0.5)
        
        ids = [f"{pdf_file}_{i}" for i in range(len(chunks))]
        
        collection.add(embeddings=all_embeddings, documents=chunks, ids=ids)
    
    return collection
