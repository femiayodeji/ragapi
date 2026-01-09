import os
from dotenv import load_dotenv

load_dotenv()
os.environ["ANONYMIZED_TELEMETRY"] = "False"

PDF_DIR = "documents"
CHROMA_DIR = "chroma_db"
PROCESSED_FILES = "processed_files.txt"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
TOP_K = int(os.getenv("TOP_K", "3"))

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

SESSION_BACKEND = os.getenv("SESSION_BACKEND", "redis")
SESSION_EXPIRE = int(os.getenv("SESSION_EXPIRE", "3600"))
SESSION_MAX_HISTORY = int(os.getenv("SESSION_MAX_HISTORY", "10"))
SESSION_KEY_PREFIX = os.getenv("SESSION_KEY_PREFIX", "session:")

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

VOICE_DIR = os.getenv("VOICE_DIR", "voices")
VOICE_EXTENSION = ".onnx"
AUDIO_EXTENSION = ".wav"

PROVIDER_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "anthropic": "https://api.anthropic.com/v1",
    "jinaai": "https://api.jina.ai/v1",
    "ollama": "http://localhost:11434"
}