import whisper
import tempfile
import os
from config import WHISPER_MODEL, AUDIO_EXTENSION


class STTService:
    def __init__(self):
        print(f"Loading Whisper {WHISPER_MODEL}")
        self.model = whisper.load_model(WHISPER_MODEL)
    
    def transcribe(self, audio_bytes: bytes) -> dict:
        with tempfile.NamedTemporaryFile(delete=False, suffix=AUDIO_EXTENSION) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            result = self.model.transcribe(temp_path)
            return {
                "text": result["text"].strip(),
                "success": True
            }
        except Exception as error:
            return {"text": "", "success": False, "error": str(error)}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)