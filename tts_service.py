import subprocess
import os
import tempfile
from config import VOICE_DIR, VOICE_EXTENSION, AUDIO_EXTENSION


class TTSService:
    def __init__(self, voice_model="en_US-lessac-medium"):
        self.model_path = f"{VOICE_DIR}/{voice_model}{VOICE_EXTENSION}"
        try:
            subprocess.run(["piper", "--version"], capture_output=True, check=True)
            print(f"Piper TTS with {voice_model}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("WARNING: Piper not found")
    
    def synthesize(self, text: str) -> dict:
        if not os.path.exists(self.model_path):
            return {"audio_bytes": None, "success": False, "error": "Model not found"}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=AUDIO_EXTENSION) as f:
            output_file = f.name
        
        try:
            process = subprocess.Popen(
                ["piper", "--model", self.model_path, "--output_file", output_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(input=text.encode('utf-8'))
            
            if process.returncode == 0:
                with open(output_file, "rb") as f:
                    audio_bytes = f.read()
                os.remove(output_file)
                return {"audio_bytes": audio_bytes, "success": True}
            else:
                return {"audio_bytes": None, "success": False, "error": stderr.decode('utf-8')}
        except Exception as error:
            return {"audio_bytes": None, "success": False, "error": str(error)}
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)