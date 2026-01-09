from openai import OpenAI
from config import LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE, LLM_API_KEY, LLM_BASE_URL, PROVIDER_URLS


class LLMClient:
    def __init__(self):
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
        self.client = self._initialize()
        
    def _initialize(self):
        api_key = LLM_API_KEY
        base_url = LLM_BASE_URL
        
        if LLM_PROVIDER == "ollama":
            base_url = base_url or PROVIDER_URLS["ollama"]
            base_url = f"{base_url}/v1"
            api_key = api_key or "ollama"
        elif LLM_PROVIDER == "openai":
            if not api_key:
                raise ValueError("LLM_API_KEY required for OpenAI")
            base_url = None
        elif LLM_PROVIDER in PROVIDER_URLS:
            if not api_key:
                raise ValueError(f"LLM_API_KEY required for {LLM_PROVIDER}")
            base_url = base_url or PROVIDER_URLS[LLM_PROVIDER]
        else:
            if not base_url:
                raise ValueError(f"LLM_BASE_URL required for {LLM_PROVIDER}")
            if not api_key:
                raise ValueError(f"LLM_API_KEY required for {LLM_PROVIDER}")
        
        return OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    
    def generate(self, prompt: str, system_message: str = None) -> str:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as error:
            raise Exception(f"LLM Error ({LLM_PROVIDER}): {str(error)}")
    
    def generate_stream(self, prompt: str, system_message: str = None):
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as error:
            raise Exception(f"LLM Error ({LLM_PROVIDER}): {str(error)}")


def get_llm_client():
    return LLMClient()
