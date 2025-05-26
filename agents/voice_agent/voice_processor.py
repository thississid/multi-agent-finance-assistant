from typing import Dict, Any, Optional
import whisper
from TTS.api import TTS
import numpy as np
import soundfile as sf
import tempfile
import os
from pathlib import Path
import torch
from ..base_agent import BaseAgent

class VoiceProcessor(BaseAgent):
    """Agent responsible for handling voice processing (STT and TTS)."""
    
    def __init__(self, name: str = "voice_processor", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.whisper_model = None
        self.tts_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.temp_dir = Path(tempfile.gettempdir()) / "voice_processor"
        self.temp_dir.mkdir(exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize STT and TTS models."""
        try:
            # Initialize Whisper model for STT
            self.whisper_model = whisper.load_model("base")
            
            # Initialize TTS model
            self.tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice data for STT or generate speech from text."""
        try:
            operation = input_data.get("operation")
            
            if operation == "stt":
                return await self._speech_to_text(input_data)
            elif operation == "tts":
                return await self._text_to_speech(input_data)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _speech_to_text(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert speech to text using Whisper."""
        try:
            audio_data = input_data.get("audio_data")
            if audio_data is None:
                raise ValueError("No audio data provided")
            
            # Save audio data to temporary file
            temp_audio_path = self.temp_dir / f"temp_audio_{os.urandom(4).hex()}.wav"
            sf.write(str(temp_audio_path), audio_data, 16000)
            
            # Transcribe audio
            result = self.whisper_model.transcribe(str(temp_audio_path))
            
            # Clean up
            temp_audio_path.unlink()
            
            return {
                "text": result["text"],
                "confidence": result.get("confidence", 1.0),
                "language": result.get("language", "en")
            }
            
        except Exception as e:
            self.logger.error(f"Speech-to-text error: {str(e)}")
            return {"error": str(e)}
    
    async def _text_to_speech(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert text to speech using TTS."""
        try:
            text = input_data.get("text")
            if not text:
                raise ValueError("No text provided")
            
            # Generate unique filename for the audio
            output_path = self.temp_dir / f"tts_output_{os.urandom(4).hex()}.wav"
            
            # Generate speech
            self.tts_model.tts_to_file(
                text=text,
                file_path=str(output_path)
            )
            
            # Read the generated audio file
            audio_data, sample_rate = sf.read(str(output_path))
            
            # Clean up
            output_path.unlink()
            
            return {
                "audio_data": audio_data,
                "sample_rate": sample_rate,
                "duration": len(audio_data) / sample_rate
            }
            
        except Exception as e:
            self.logger.error(f"Text-to-speech error: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Clean up temporary files and resources."""
        try:
            # Clean up any remaining temporary files
            for file in self.temp_dir.glob("*"):
                file.unlink()
            self.temp_dir.rmdir()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for processing."""
        if "operation" not in input_data:
            return False
            
        if input_data["operation"] == "stt":
            return "audio_data" in input_data
        elif input_data["operation"] == "tts":
            return "text" in input_data
            
        return False 