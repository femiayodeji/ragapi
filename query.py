from typing import List
import os
from openai import OpenAI
import re
import time

from config import JINA_API_KEY, JINA_BASE_URL, JINA_MODEL, GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL, TOP_K, PDF_DIR

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided document context.

IMPORTANT GUIDELINES:

1. OUT-OF-SCOPE QUERIES:
   - If the question is unrelated to the document context, politely inform the user
   - Example: "I can only answer questions based on the provided documents"

2. VAGUE/AMBIGUOUS QUERIES:
   - For greetings, respond warmly and prompt for specific questions
   - For vague questions, ask for clarification

3. ANSWERING QUESTIONS:
   - Base answers ONLY on the provided context
   - Keep responses concise (mostly 1 paragraph, and 2-3 paragraphs max if the context is very relevant)
   - Use bullet points for lists or steps
   - If context doesn't contain the answer, say so clearly

4. TONE: Professional, clear, and helpful"""

jina_client = OpenAI(base_url=JINA_BASE_URL, api_key=JINA_API_KEY)
llm_client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY)

def get_embeddings(texts: List[str]) -> List[List[float]]:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = jina_client.embeddings.create(input=texts, model=JINA_MODEL)
            return [e.embedding for e in response.data]
        except Exception as e:
            if "RateLimitError" in str(type(e)) or "429" in str(e):
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
            raise

def get_document_names() -> List[str]:
    try:
        return sorted([f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')])
    except FileNotFoundError:
        return []

def format_document_scope() -> str:
    doc_names = get_document_names()
    if not doc_names:
        return "- None"
    return "\n".join([f"- {name}" for name in doc_names])

def build_system_prompt() -> str:
    scope = format_document_scope()
    return f"{SYSTEM_PROMPT}\n\nDocument scope:\n{scope}"

def search(collection, query: str) -> str:
    query_embedding = get_embeddings([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=TOP_K)
    return "\n\n".join(results['documents'][0]) if results['documents'] else ""

def stream_response(question: str, context: str, history: List[dict]):
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-10:]])
    prompt = f"Context:\n{context}\n\nHistory:\n{history_text}\n\nQuestion: {question}"
    system_prompt = build_system_prompt()
    
    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )
    
    in_thinking = False
    for chunk in response:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            
            if "<think>" in content:
                in_thinking = True
                content = content.split("<think>")[0]
            
            if "</think>" in content:
                in_thinking = False
                content = content.split("</think>")[-1]
            
            if not in_thinking and content:
                yield content
