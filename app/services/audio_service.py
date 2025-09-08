# app/services/audio_service.py
import whisper
import torch
import numpy as np
import librosa
import soundfile as sf
import tempfile
import os
from datetime import datetime
import time
from config import Config
from logger_config import get_logger, AudioLogger

class WhisperSTTService:
    """Speech-to-Text service using OpenAI Whisper"""
    
    def __init__(self):
        self.logger = get_logger("whisper_stt")
        self.audio_logger = AudioLogger("whisper_stt")
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            self.audio_logger.log_audio_start("Loading Whisper model", Config.WHISPER_MODEL)
            start_time = time.time()
            
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self.logger.info(f"🔧 Using device: {device}")
            
            # Load the model
            self.model = whisper.load_model(Config.WHISPER_MODEL, device=device)
            
            load_time = time.time() - start_time
            self.audio_logger.log_audio_success("Whisper model loading", load_time)
            
        except Exception as e:
            self.audio_logger.log_audio_error("Whisper model loading", e)
            raise
    
    def transcribe_audio_file(self, audio_file_path, language=None):
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path (str): Path to audio file
            language (str, optional): Language code (e.g., 'en', 'es')
        
        Returns:
            dict: Transcription result with text and confidence
        """
        try:
            self.audio_logger.log_audio_start("Audio transcription", audio_file_path)
            start_time = time.time()
            
            # Transcribe the audio
            if language:
                result = self.model.transcribe(audio_file_path, language=language)
            else:
                result = self.model.transcribe(audio_file_path)
            
            transcription_time = time.time() - start_time
            
            # Extract text and confidence
            text = result["text"].strip()
            language_detected = result.get("language", "unknown")
            
            self.audio_logger.log_audio_success("Audio transcription", transcription_time)
            self.logger.info(f"📝 Transcribed text length: {len(text)} characters")
            self.logger.info(f"🌍 Detected language: {language_detected}")
            
            return {
                "text": text,
                "language": language_detected,
                "duration": transcription_time,
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            self.audio_logger.log_audio_error("Audio transcription", e)
            raise
    
    def transcribe_audio_bytes(self, audio_bytes, filename="temp_audio.wav"):
        """
        Transcribe audio from bytes data
        
        Args:
            audio_bytes (bytes): Audio data in bytes
            filename (str): Temporary filename for processing
        
        Returns:
            dict: Transcription result
        """
        temp_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)
            
            # Transcribe the temporary file
            result = self.transcribe_audio_file(temp_path)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error transcribing audio bytes: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    
    def process_realtime_audio(self, audio_data, sample_rate=16000):
        """
        Process real-time audio data
        
        Args:
            audio_data (np.array): Audio data as numpy array
            sample_rate (int): Sample rate of the audio
        
        Returns:
            dict: Transcription result
        """
        try:
            self.audio_logger.log_audio_start("Real-time audio processing")
            
            # Ensure audio is in the right format
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)  # Convert stereo to mono
            
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            
            # Resample if necessary
            if sample_rate != 16000:
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
            
            # Create temporary file for Whisper
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_path = temp_file.name
                sf.write(temp_path, audio_data, 16000)
            
            try:
                result = self.transcribe_audio_file(temp_path)
                return result
            finally:
                os.remove(temp_path)
                
        except Exception as e:
            self.audio_logger.log_audio_error("Real-time audio processing", e)
            raise
    
    def get_model_info(self):
        """Get information about the loaded model"""
        return {
            "model_name": Config.WHISPER_MODEL,
            "device": next(self.model.parameters()).device.type if self.model else "unknown",
            "model_size": Config.WHISPER_MODEL
        }