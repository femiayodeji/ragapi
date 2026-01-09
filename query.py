from config import TOP_K
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