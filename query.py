from config import TOP_K, SESSION_MAX_HISTORY
from llm_client import get_llm_client


SYSTEM_PROMPT = """Government service assistant. Help citizens clearly and efficiently.

If conversation history exists (marked with ===), use it naturally.
Keep answers concise (2-3 paragraphs max), use bullet points for steps.
Base answers on official documents only."""


def create_rag_chain(vectorstore):
    if not vectorstore:
        return None
    return {
        "vectorstore": vectorstore,
        "llm": get_llm_client()
    }


def get_session_context(session_service, session_id: str):
    if not session_service:
        return None
    
    try:
        if session_service.session_exists(session_id):
            return session_service.format_history(session_id, SESSION_MAX_HISTORY)
    except Exception:
        return None


def save_session_message(session_service, session_id: str, role: str, content: str):
    if session_service:
        try:
            session_service.add_message(session_id, role, content)
        except Exception:
            pass


def query_with_session(rag_chain, session_service, question: str, session_id: str):
    session_context = get_session_context(session_service, session_id)
    save_session_message(session_service, session_id, "user", question)
    
    answer = query_documents(rag_chain, question, session_context)
    
    save_session_message(session_service, session_id, "assistant", answer)
    
    return {"question": question, "answer": answer, "session_id": session_id}


def query_with_session_stream(rag_chain, session_service, question: str, session_id: str):
    session_context = get_session_context(session_service, session_id)
    save_session_message(session_service, session_id, "user", question)
    
    full_answer = ""
    for chunk in query_documents_stream(rag_chain, question, session_context):
        full_answer += chunk
        yield chunk
    
    save_session_message(session_service, session_id, "assistant", full_answer)


def query_documents(qa_chain, question: str, session_context: str = None) -> str:
    if not qa_chain:
        raise ValueError("QA chain not initialized")
    
    vectorstore = qa_chain["vectorstore"]
    llm = qa_chain["llm"]
    
    docs = vectorstore.as_retriever(search_kwargs={"k": TOP_K}).invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    user_prompt = ""
    if session_context:
        user_prompt += f"=== CONVERSATION HISTORY ===\n{session_context}\n=== END ===\n\n"
    
    user_prompt += f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    
    return llm.generate(user_prompt, SYSTEM_PROMPT)


def query_documents_stream(qa_chain, question: str, session_context: str = None):
    if not qa_chain:
        raise ValueError("QA chain not initialized")
    
    vectorstore = qa_chain["vectorstore"]
    llm = qa_chain["llm"]
    
    docs = vectorstore.as_retriever(search_kwargs={"k": TOP_K}).invoke(question)
    context = "\n\n".join([doc.page_content for doc in docs])
    
    user_prompt = ""
    if session_context:
        user_prompt += f"=== CONVERSATION HISTORY ===\n{session_context}\n=== END ===\n\n"
    
    user_prompt += f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    
    for chunk in llm.generate_stream(user_prompt, SYSTEM_PROMPT):
        yield chunk