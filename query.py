from config import TOP_K, SESSION_MAX_HISTORY
from llm_client import get_llm_client
from query_validator import validator
from typing import List


SYSTEM_PROMPT = """You are a helpful government service assistant specializing in passport and immigration services.

Your knowledge base contains: {doc_titles}

IMPORTANT GUIDELINES:

1. OUT-OF-SCOPE QUERIES:
   - If the question is unrelated to the documents above (e.g., weather, sports, general knowledge), politely redirect:
     "I can only help with {service_scope}. Your question about [topic] is outside my knowledge base.
     Could you ask something related to passport applications, requirements, or procedures?"

2. VAGUE/AMBIGUOUS QUERIES:
   - For greetings ("hi", "hello"), respond warmly and prompt for specific questions
   - For vague questions ("help", "what do I need?"), ask for clarification:
     "I'd be happy to help! Could you be more specific? For example:
     • What documents do I need for passport renewal?
     • How long does the application process take?
     • What are the fees for expedited service?"

3. ANSWERING QUESTIONS:
   - Base answers ONLY on the provided context
   - Keep responses concise (2-3 paragraphs max)
   - Use bullet points for lists or steps
   - If conversation history exists (marked with ===), reference it naturally
   - If context doesn't contain the answer, say so clearly

4. TONE: Professional, clear, and helpful"""


def get_system_prompt(doc_titles: List[str]) -> str:
    titles_str = ", ".join(doc_titles) if doc_titles else "passport and government services"
    service_scope = titles_str.lower().replace(" - ", " for ")
    return SYSTEM_PROMPT.format(doc_titles=titles_str, service_scope=service_scope)


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
    
    basic_error = validator.validate_basic(question)
    if basic_error:
        return basic_error
    
    vectorstore = qa_chain["vectorstore"]
    llm = qa_chain["llm"]
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    docs = retriever.invoke(question)
    
    doc_titles = []
    if docs:
        for doc in docs:
            source = doc.metadata.get('source', '')
            if source:
                filename = source.split('/')[-1].replace('.pdf', '').replace('_', ' ').title()
                if filename not in doc_titles:
                    doc_titles.append(filename)
    
    if not docs:
        return (
            "I couldn't find any relevant information in my knowledge base. "
            "Please ask questions related to passport and government services."
        )
    
    context = "\n\n".join([doc.page_content for doc in docs])
    system_prompt = get_system_prompt(doc_titles)
    
    user_prompt = ""
    if session_context:
        user_prompt += f"=== CONVERSATION HISTORY ===\n{session_context}\n=== END ===\n\n"
    
    user_prompt += f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    
    return llm.generate(user_prompt, system_prompt)


def query_documents_stream(qa_chain, question: str, session_context: str = None):
    if not qa_chain:
        raise ValueError("QA chain not initialized")
    
    basic_error = validator.validate_basic(question)
    if basic_error:
        yield basic_error
        return
    
    vectorstore = qa_chain["vectorstore"]
    llm = qa_chain["llm"]
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    docs = retriever.invoke(question)
    
    doc_titles = []
    if docs:
        for doc in docs:
            source = doc.metadata.get('source', '')
            if source:
                filename = source.split('/')[-1].replace('.pdf', '').replace('_', ' ').title()
                if filename not in doc_titles:
                    doc_titles.append(filename)
    
    if not docs:
        yield (
            "I couldn't find any relevant information in my knowledge base. "
            "Please ask questions related to passport and government services."
        )
        return
    
    context = "\n\n".join([doc.page_content for doc in docs])
    system_prompt = get_system_prompt(doc_titles)
    
    user_prompt = ""
    if session_context:
        user_prompt += f"=== CONVERSATION HISTORY ===\n{session_context}\n=== END ===\n\n"
    
    user_prompt += f"Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    
    for chunk in llm.generate_stream(user_prompt, system_prompt):
        yield chunk
        yield chunk