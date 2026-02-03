import os
import subprocess
import struct
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, VOICE_DIR

whisper_model = None

def init_whisper():
    global whisper_model
    whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")

def transcribe(audio_bytes: bytes) -> str:
    segments, _ = whisper_model.transcribe(audio_bytes, beam_size=5)
    return " ".join([segment.text for segment in segments])

def text_to_speech(text: str) -> bytes:
    voice_path = os.path.join(VOICE_DIR, "en_US-lessac-medium.onnx")
    result = subprocess.run(
        ["piper/piper/piper", "--model", voice_path, "--output-raw"],
        input=text.encode(),
        capture_output=True,
        check=False
    )
    
    if result.returncode != 0:
        error_msg = result.stderr.decode() if result.stderr else "Unknown error"
        raise RuntimeError(f"Piper TTS failed: {error_msg}")
    
    if not result.stdout:
        raise RuntimeError("Piper TTS produced no audio output")
    
    pcm_data = result.stdout
    sample_rate = 22050
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_data)
    
    wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        data_size + 36,
        b'WAVE',
        b'fmt ',
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    
    return wav_header + pcm_data
