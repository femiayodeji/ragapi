"""
Document Processing and Vector Store Management

This module handles:
- PDF document loading and chunking
- ChromaDB vector store creation and management
- Tracking processed documents to avoid reprocessing
- Embedding configuration management

Key Functions:
- process_pdfs(): Main entry point for processing new PDFs
- load_vectorstore(): Load existing vector store
- create_vectorstore(): Create new vector store from documents
- clear_all(): Reset all data (use when changing embedding models)

Note: Changing embedding models requires clearing the vector store
since embeddings from different models are incompatible.
"""

import os
import hashlib
import shutil
from typing import List, Tuple
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import CHROMA_DIR, PROCESSED_FILES, PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from embedding_client import get_embeddings


def file_hash(filepath: str) -> str:
    """Generate MD5 hash of file to detect changes."""
    with open(filepath, 'rb') as file_handle:
        return hashlib.md5(file_handle.read()).hexdigest()


def load_processed_files() -> set[str]:
    if os.path.exists(PROCESSED_FILES):
        with open(PROCESSED_FILES, 'r') as file_handle:
            return set(line.strip() for line in file_handle)
    return set()


def save_processed_file(file_hash: str, filename: str):
    with open(PROCESSED_FILES, 'a') as file_handle:
        file_handle.write(f"{file_hash}:{filename}\n")


def get_pdf_files() -> List[str]:
    os.makedirs(PDF_DIR, exist_ok=True)
    return [f for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]


def get_unprocessed_pdfs() -> List[Tuple[str, str, str]]:
    processed = load_processed_files()
    unprocessed = []
    
    for pdf_file in get_pdf_files():
        filepath = os.path.join(PDF_DIR, pdf_file)
        hash_value = file_hash(filepath)
        if not any(hash_value in record for record in processed):
            unprocessed.append((filepath, hash_value, pdf_file))
    
    return unprocessed


def create_vectorstore(documents, embeddings=None):
    return Chroma.from_documents(
        documents=documents,
        embedding=embeddings or get_embeddings(),
        persist_directory=CHROMA_DIR
    )


def load_vectorstore(embeddings=None):
    """Load existing ChromaDB vector store."""
    if not os.path.exists(CHROMA_DIR):
        return None
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings or get_embeddings()
    )


def chunk_count(vectorstore) -> int:
    """Get number of document chunks in vector store."""
    return vectorstore._collection.count() if vectorstore else 0


def clear_all():
    """
    Clear all data: vector store, processed files, and embedding config.
    
    WARNING: This deletes all processed documents and requires reprocessing.
    Use when:
    - Changing embedding models (different embeddings are incompatible)
    - Starting fresh with new documents
    - Troubleshooting vector store issues
    """
    for path in [CHROMA_DIR, PROCESSED_FILES, '.embedding_config']:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)


def save_embedding_config(provider: str, model: str):
    """
    Save embedding configuration to detect model changes.
    
    This tracks which embedding provider/model was used to create the vector store.
    If the config changes, we know to rebuild the vector store since embeddings
    from different models cannot be mixed.
    """
    with open('.embedding_config', 'w') as f:
        f.write(f"{provider}:{model}")


def load_embedding_config() -> Tuple[str, str]:
    """Load saved embedding configuration, returns (provider, model) or (None, None)."""
    if os.path.exists('.embedding_config'):
        with open('.embedding_config', 'r') as f:
            content = f.read().strip()
            if ':' in content:
                return tuple(content.split(':', 1))
    return None, None


def embedding_changed(provider: str, model: str) -> bool:
    saved_provider, saved_model = load_embedding_config()
    return saved_provider and (saved_provider != provider or saved_model != model)


def process_pdf(filepath: str, filename: str, hash_value: str) -> List[Document]:
    print(f"Processing {filename}")
    loader = PyPDFLoader(filepath)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(loader.load())
    save_processed_file(hash_value, filename)
    print(f"Created {len(chunks)} chunks")
    return chunks


def process_pdfs() -> List[Document]:
    unprocessed = get_unprocessed_pdfs()
    if not unprocessed:
        return []
    
    print(f"Processing {len(unprocessed)} PDF(s)")
    chunks = []
    for filepath, hash_value, filename in unprocessed:
        chunks.extend(process_pdf(filepath, filename, hash_value))
    return chunks