import requests
from typing import List
from openai import OpenAI
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.embeddings import Embeddings

from app.config import (EMBEDDING_MODEL, EMBEDDING_PROVIDER, LLM_PROVIDER, 
                   EMBEDDING_API_KEY, EMBEDDING_BASE_URL, LLM_API_KEY, LLM_BASE_URL, PROVIDER_URLS)


class UniversalEmbeddings(Embeddings):
    def __init__(self):
        self.provider = EMBEDDING_PROVIDER or LLM_PROVIDER
        self.model = EMBEDDING_MODEL
        self._initialize()
    
    def _initialize(self):
        api_key = EMBEDDING_API_KEY or LLM_API_KEY
        base_url = EMBEDDING_BASE_URL or LLM_BASE_URL
        
        if self.provider == "ollama":
            self.client = OllamaEmbeddings(
                model=self.model,
                base_url=base_url or PROVIDER_URLS["ollama"]
            )
            self.type = "ollama"
        elif self.provider == "openai":
            if not api_key:
                raise ValueError("EMBEDDING_API_KEY required for OpenAI")
            self.client = OpenAI(api_key=api_key)
            self.type = "openai"
        elif self.provider == "gemini":
            if not api_key:
                raise ValueError("EMBEDDING_API_KEY required for Gemini")
            self.client = OpenAI(
                base_url=base_url or PROVIDER_URLS["gemini"],
                api_key=api_key
            )
            self.type = "openai"
        elif self.provider == "jinaai":
            if not api_key:
                raise ValueError("EMBEDDING_API_KEY required for Jina AI")
            self.api_key = api_key
            self.base_url = base_url or PROVIDER_URLS["jinaai"]
            self.type = "jinaai"
        else:
            if not base_url or not api_key:
                raise ValueError(f"EMBEDDING_BASE_URL and EMBEDDING_API_KEY required for {self.provider}")
            self.client = OpenAI(base_url=base_url, api_key=api_key)
            self.type = "openai"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.type == "ollama":
            return self.client.embed_documents(texts)
        elif self.type == "jinaai":
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "input": texts}
            )
            response.raise_for_status()
            return [item["embedding"] for item in response.json()["data"]]
        else:
            response = self.client.embeddings.create(model=self.model, input=texts)
            return [item.embedding for item in response.data]
    
    def embed_query(self, text: str) -> List[float]:
        if self.type == "ollama":
            return self.client.embed_query(text)
        elif self.type == "jinaai":
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": self.model, "input": [text]}
            )
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        else:
            response = self.client.embeddings.create(model=self.model, input=[text])
            return response.data[0].embedding


def get_embeddings():
    return UniversalEmbeddings()
