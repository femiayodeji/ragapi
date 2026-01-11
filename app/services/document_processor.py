import os
import hashlib
import shutil
from typing import List, Tuple
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.config import CHROMA_DIR, PROCESSED_FILES, PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from app.clients.embedding_client import get_embeddings

# Track vectorstore for caching
_vectorstore = None


def file_hash(filepath: str) -> str:
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
    if not os.path.exists(CHROMA_DIR):
        return None
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings or get_embeddings()
    )


def chunk_count(vectorstore) -> int:
    return vectorstore._collection.count() if vectorstore else 0


def clear_all():
    for path in [CHROMA_DIR, PROCESSED_FILES, '.embedding_config']:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.exists(path):
            os.remove(path)


def save_embedding_config(provider: str, model: str):
    with open('.embedding_config', 'w') as f:
        f.write(f"{provider}:{model}")


def load_embedding_config() -> Tuple[str, str]:
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


def load_documents():
    from app.config import EMBEDDING_MODEL, EMBEDDING_PROVIDER, LLM_PROVIDER
    from app.core import query
    
    provider = EMBEDDING_PROVIDER or LLM_PROVIDER
    embeddings = get_embeddings()
    
    if embedding_changed(provider, EMBEDDING_MODEL):
        old_provider, old_model = load_embedding_config()
        print(f"Embedding changed: {old_provider}/{old_model} → {provider}/{EMBEDDING_MODEL}")
        print("Clearing old database")
        clear_all()
    
    pdf_files = get_pdf_files()
    if not pdf_files:
        print(f"No PDFs in '{PDF_DIR}'")
        return None, None
    
    print(f"Found {len(pdf_files)} PDF(s)")
    
    vectorstore = load_vectorstore(embeddings)
    chunks = process_pdfs()
    
    if chunks:
        if vectorstore:
            print(f"Adding {len(chunks)} new chunks")
            vectorstore.add_documents(chunks)
        else:
            print(f"Creating vectorstore with {len(chunks)} chunks")
            vectorstore = create_vectorstore(chunks, embeddings)
    elif vectorstore:
        count = chunk_count(vectorstore)
        print(f"Loaded {count} chunks")
    
    global _vectorstore
    _vectorstore = vectorstore
    
    rag_chain = query.create_rag_chain(vectorstore) if vectorstore else None
    if rag_chain:
        save_embedding_config(provider, EMBEDDING_MODEL)
    
    return vectorstore, rag_chain


def reload_documents():
    global _vectorstore
    from app.core import query as query_module
    
    vectorstore, rag_chain = load_documents()
    _vectorstore = vectorstore
    
    query_module.cached_vector_search.cache_clear()
    
    return vectorstore, rag_chain, chunk_count(vectorstore)