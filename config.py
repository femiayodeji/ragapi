import os
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_BASE_URL = os.getenv("JINA_BASE_URL", "https://api.jina.ai/v1")
JINA_MODEL = os.getenv("JINA_MODEL", "jina-embeddings-v3")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

PDF_DIR = "data/documents"
CHROMA_DIR = "storage/chroma_db"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 3

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
VOICE_DIR = "voices"
