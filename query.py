from typing import List
from openai import OpenAI
import re
import time

from config import JINA_API_KEY, JINA_BASE_URL, JINA_MODEL, GROQ_API_KEY, GROQ_BASE_URL, LLM_MODEL, TOP_K

SYSTEM_PROMPT = """You are a helpful government service assistant specializing in passport and immigration services.

IMPORTANT GUIDELINES:

1. OUT-OF-SCOPE QUERIES:
   - If the question is unrelated to passport/immigration, politely redirect
   - Example: "I can only help with passport and immigration services"

2. VAGUE/AMBIGUOUS QUERIES:
   - For greetings, respond warmly and prompt for specific questions
   - For vague questions, ask for clarification

3. ANSWERING QUESTIONS:
   - Base answers ONLY on the provided context
   - Keep responses concise (2-3 paragraphs max)
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

def search(collection, query: str) -> str:
    query_embedding = get_embeddings([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=TOP_K)
    return "\n\n".join(results['documents'][0]) if results['documents'] else ""

def stream_response(question: str, context: str, history: List[dict]):
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history[-10:]])
    prompt = f"Context:\n{context}\n\nHistory:\n{history_text}\n\nQuestion: {question}"
    
    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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

def generate_response(question: str, context: str) -> str:
    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ],
    )
    content = response.choices[0].message.content
    return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
