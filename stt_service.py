from faster_whisper import WhisperModel
import tempfile
import os
from config import WHISPER_MODEL, AUDIO_EXTENSION


class STTService:
    def __init__(self):
        print(f"Loading Whisper {WHISPER_MODEL}")
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    
    def transcribe(self, audio_bytes: bytes) -> dict:
        with tempfile.NamedTemporaryFile(delete=False, suffix=AUDIO_EXTENSION) as f:
            f.write(audio_bytes)
            temp_path = f.name
        
        try:
            segments, info = self.model.transcribe(temp_path)
            text = "".join([segment.text for segment in segments]).strip()
            return {
                "text": text,
                "success": True
            }
        except Exception as error:
            return {"text": "", "success": False, "error": str(error)}
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)