import subprocess
import os
import tempfile
from pathlib import Path
from config import VOICE_DIR, VOICE_EXTENSION, AUDIO_EXTENSION


class TTSService:
    def __init__(self, voice_model="en_US-lessac-medium"):
        self.model_path = f"{VOICE_DIR}/{voice_model}{VOICE_EXTENSION}"
        self.piper_dir = Path(__file__).parent / "piper"
        self.piper_executable = self._find_piper_executable()
        self.env = self._setup_environment()
        
        try:
            subprocess.run([self.piper_executable, "--version"], capture_output=True, check=True, env=self.env)
            print(f"Piper TTS with {voice_model}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("WARNING: Piper not found")
    
    def _find_piper_executable(self):
        possible_paths = [
            "piper",
            "/usr/local/bin/piper",
            "/usr/bin/piper",
            str(Path(__file__).parent / "piper" / "piper" / "piper"),
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run([path, "--version"], capture_output=True, timeout=2)
                if result.returncode == 0:
                    return path
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return "piper"
    
    def _setup_environment(self):
        env = os.environ.copy()
        if self.piper_dir.exists():
            ld_library_path = str(self.piper_dir)
            if "LD_LIBRARY_PATH" in env:
                env["LD_LIBRARY_PATH"] = f"{ld_library_path}:{env['LD_LIBRARY_PATH']}"
            else:
                env["LD_LIBRARY_PATH"] = ld_library_path
            
            espeak_data = self.piper_dir / "espeak-ng-data"
            if espeak_data.exists():
                env["ESPEAK_DATA_PATH"] = str(espeak_data)
        return env
    
    def synthesize(self, text: str) -> dict:
        if not os.path.exists(self.model_path):
            return {"audio_bytes": None, "success": False, "error": "Model not found"}
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=AUDIO_EXTENSION) as f:
            output_file = f.name
        
        try:
            process = subprocess.Popen(
                [self.piper_executable, "--model", self.model_path, "--output_file", output_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env
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