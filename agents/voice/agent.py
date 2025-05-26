from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, Optional
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
from TTS.api import TTS
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

app = FastAPI(title="Voice Processing Agent")

# Initialize Whisper model
model = whisper.load_model(os.getenv("WHISPER_MODEL", "base"))

# Initialize TTS model
tts = TTS(model_name=os.getenv("TTS_MODEL", "tts_models/en/ljspeech/tacotron2-DDC"))

class AudioRequest(BaseModel):
    audio_data: bytes
    sample_rate: int = 16000

class TextRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None

class TranscriptionResponse(BaseModel):
    text: str
    confidence: float

class SynthesisResponse(BaseModel):
    audio_data: bytes
    sample_rate: int

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """Convert speech to text using Whisper."""
    try:
        # Save uploaded audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(await audio.read())
            temp_audio_path = temp_audio.name
        
        # Transcribe audio
        result = model.transcribe(temp_audio_path)
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
        return TranscriptionResponse(
            text=result["text"],
            confidence=result.get("confidence", 0.0)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(request: TextRequest):
    """Convert text to speech using TTS."""
    try:
        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # Generate speech
        tts.tts_to_file(text=request.text, file_path=temp_audio_path)
        
        # Read generated audio file
        audio_data, sample_rate = sf.read(temp_audio_path)
        
        # Clean up temporary file
        os.unlink(temp_audio_path)
        
        return SynthesisResponse(
            audio_data=audio_data.tobytes(),
            sample_rate=sample_rate
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record")
async def record_audio(duration: int = 5):
    """Record audio from microphone."""
    try:
        # Record audio
        sample_rate = 16000
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        return {
            "audio_data": recording.tobytes(),
            "sample_rate": sample_rate
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("VOICE_AGENT_PORT", 8006))) 