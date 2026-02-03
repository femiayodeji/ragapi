import os
from typing import List
from pypdf import PdfReader
from chromadb import Client
from chromadb.config import Settings

from config import PDF_DIR, CHROMA_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from query import get_embeddings

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
    
    chroma_client = Client(Settings(persist_directory=CHROMA_DIR, anonymized_telemetry=False))
    collection = chroma_client.get_or_create_collection("documents")
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        return collection
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        reader = PdfReader(pdf_path)
        text = " ".join([page.extract_text() for page in reader.pages])
        chunks = chunk_text(text)
        
        embeddings = get_embeddings(chunks)
        ids = [f"{pdf_file}_{i}" for i in range(len(chunks))]
        
        collection.add(embeddings=embeddings, documents=chunks, ids=ids)
    
    return collection
