import os
import document_processor
import query
from config import PDF_DIR, EMBEDDING_MODEL, EMBEDDING_PROVIDER, LLM_PROVIDER


def load_documents():
    provider = EMBEDDING_PROVIDER or LLM_PROVIDER
    embeddings = document_processor.get_embeddings()
    
    if document_processor.embedding_changed(provider, EMBEDDING_MODEL):
        old_provider, old_model = document_processor.load_embedding_config()
        print(f"Embedding changed: {old_provider}/{old_model} → {provider}/{EMBEDDING_MODEL}")
        print("Clearing old database")
        document_processor.clear_all()
    
    pdf_files = document_processor.get_pdf_files()
    if not pdf_files:
        print(f"No PDFs in '{PDF_DIR}'")
        return None, None
    
    print(f"Found {len(pdf_files)} PDF(s)")
    
    vectorstore = document_processor.load_vectorstore(embeddings)
    chunks = document_processor.process_pdfs()
    
    if chunks:
        if vectorstore:
            print(f"Adding {len(chunks)} new chunks")
            vectorstore.add_documents(chunks)
        else:
            print(f"Creating vectorstore with {len(chunks)} chunks")
            vectorstore = document_processor.create_vectorstore(chunks, embeddings)
    elif vectorstore:
        count = document_processor.chunk_count(vectorstore)
        print(f"Loaded {count} chunks")
    
    rag_chain = query.create_rag_chain(vectorstore) if vectorstore else None
    if rag_chain:
        document_processor.save_embedding_config(provider, EMBEDDING_MODEL)
    
    return vectorstore, rag_chain


def reload_documents(current_vectorstore):
    vectorstore, rag_chain = load_documents()
    return vectorstore, rag_chain, document_processor.chunk_count(vectorstore)