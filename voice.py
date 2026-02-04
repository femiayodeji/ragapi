from io import BytesIO
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment

def transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio bytes using Google Speech Recognition.
    
    Handles various audio formats and resamples to 16kHz as required by Google API.
    """
    recognizer = sr.Recognizer()
    
    try:
        # Try to load audio with pydub to handle various formats
        # and resample to 16kHz which is required by Google Speech API
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        
        # Resample to 16kHz if needed
        if audio.frame_rate != 16000:
            audio = audio.set_frame_rate(16000)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Export to raw PCM bytes
        pcm_data = audio.export(format="wav").read()
        
        # Create AudioData from PCM
        audio_data = sr.AudioData(pcm_data, sample_rate=16000, sample_width=audio.sample_width)
        
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        raise RuntimeError("Could not understand audio - try speaking more clearly or use a different audio file")
    except sr.RequestError as e:
        raise RuntimeError(f"Speech recognition service error: {e}")
    except Exception as e:
        raise RuntimeError(f"Audio processing error: {str(e)}")

def text_to_speech(text: str) -> bytes:
    """Convert text to speech using gTTS and return audio bytes."""
    tts = gTTS(text=text, lang='en', slow=False)
    audio_buffer = BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

