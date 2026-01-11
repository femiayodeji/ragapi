import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_query():
    return {"question": "What documents do I need for a passport?", "session_id": "test-123"}

@pytest.fixture
def sample_audio():
    import io
    import wave
    import struct
    
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        samples = [int(32767 * 0.5 * (i % 100) / 100) for i in range(16000)]
        wav.writeframes(struct.pack(f'{len(samples)}h', *samples))
    
    buffer.seek(0)
    return buffer
