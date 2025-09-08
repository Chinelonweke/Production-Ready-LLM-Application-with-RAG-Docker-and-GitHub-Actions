import os
import time
import tempfile
import base64
from gtts import gTTS
from config import Config
from logger_config import get_logger, AudioLogger


class GoogleTTSService:
    """Text-to-Speech service using gTTS (Google TTS) - Free Service"""

    def __init__(self):
        self.logger = get_logger("gtts")
        self.audio_logger = AudioLogger("gtts")
        self.language = "en"
        self.logger.info("🎤 GoogleTTSService initialized successfully")

    def text_to_speech_file(self, text, output_path=None, language="en"):
        """
        Convert text to speech and save as file

        Args:
            text (str): Text to convert to speech
            output_path (str, optional): Path to save the audio file
            language (str): Language code (default: "en")

        Returns:
            str: Path to the generated audio file
        """
        try:
            self.audio_logger.log_audio_start("Text-to-speech conversion")
            start_time = time.time()

            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            if output_path is None:
                output_path = tempfile.mktemp(suffix=".mp3")  # gTTS outputs mp3

            self.logger.info(f"🔄 Converting text to speech: '{text[:50]}...'")
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(output_path)

            # Verify file was created
            if not os.path.exists(output_path):
                raise Exception("Audio file was not created")

            file_size = os.path.getsize(output_path)
            conversion_time = time.time() - start_time
            
            self.audio_logger.log_audio_success("Text-to-speech conversion", conversion_time)
            self.logger.info(f"📝 Converted text length: {len(text)} characters")
            self.logger.info(f"🎵 Generated audio file: {output_path} ({file_size} bytes)")

            return output_path

        except Exception as e:
            self.audio_logger.log_audio_error("Text-to-speech conversion", e)
            self.logger.error(f"❌ Text-to-speech conversion failed: {str(e)}")
            raise

    def text_to_speech_bytes(self, text, language="en"):
        """
        Convert text to speech and return as bytes

        Args:
            text (str): Text to convert to speech
            language (str): Language code (default: "en")

        Returns:
            bytes: Audio data as bytes
        """
        temp_path = None
        try:
            self.logger.info(f"🔄 Converting text to audio bytes: '{text[:30]}...'")
            temp_path = self.text_to_speech_file(text, language=language)
            
            with open(temp_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            self.logger.info(f"✅ Generated audio bytes: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            self.logger.error(f"❌ Error converting text to speech bytes: {str(e)}")
            raise
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    self.logger.debug(f"🗑️ Cleaned up temporary file: {temp_path}")
                except Exception as cleanup_error:
                    self.logger.warning(f"⚠️ Failed to cleanup temp file: {cleanup_error}")

    def text_to_speech_base64(self, text, language="en"):
        """
        Convert text to speech and return as base64 encoded string

        Args:
            text (str): Text to convert to speech
            language (str): Language code (default: "en")

        Returns:
            str: Base64 encoded audio data
        """
        try:
            self.logger.info(f"🔄 Converting text to base64 audio: '{text[:30]}...'")
            audio_bytes = self.text_to_speech_bytes(text, language=language)
            base64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            self.logger.info(f"🔐 Generated base64 audio (length: {len(base64_audio)})")
            return base64_audio
            
        except Exception as e:
            self.logger.error(f"❌ Error converting text to base64 audio: {str(e)}")
            raise

    def get_available_languages(self):
        """Return supported languages by gTTS"""
        return {
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese"
        }

    def set_language(self, language="en"):
        """Set default language for TTS"""
        available_langs = self.get_available_languages()
        if language in available_langs:
            self.language = language
            self.logger.info(f"🌐 Language set to: {available_langs[language]} ({language})")
        else:
            self.logger.warning(f"⚠️ Language '{language}' not supported. Using English.")
            self.language = "en"

    def get_model_info(self):
        """Get information about the TTS service"""
        return {
            "engine": "Google Text-to-Speech (gTTS)",
            "cost": "Free",
            "internet_required": True,
            "supported_languages": len(self.get_available_languages()),
            "current_language": self.language,
            "output_format": "MP3",
            "quality": "Good",
            "usage_limits": "Rate limited by Google"
        }

    def health_check(self):
        """Perform a health check on the TTS service"""
        try:
            self.logger.info("🔍 Performing TTS health check...")
            
            # Test with a simple phrase
            test_text = "Health check test"
            audio_bytes = self.text_to_speech_bytes(test_text)
            
            if len(audio_bytes) > 0:
                self.logger.info("✅ TTS health check passed")
                return True
            else:
                self.logger.error("❌ TTS health check failed: No audio generated")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ TTS health check failed: {str(e)}")
            return False


class SpeechService:
    """Combined Speech Service for STT and TTS operations"""

    def __init__(self, stt_service, tts_service):
        self.stt = stt_service
        self.tts = tts_service
        self.logger = get_logger("speech_service")
        self.logger.info("🎯 SpeechService initialized with STT and TTS services")

    def voice_to_voice(self, audio_input, response_text=None, language="en"):
        """
        Complete voice-to-voice pipeline: Audio -> Text -> Text -> Audio

        Args:
            audio_input: Audio file path or audio bytes
            response_text (str, optional): Text to convert to speech response
            language (str): Language code for TTS

        Returns:
            dict: Complete voice processing results
        """
        try:
            self.logger.info("🔄 Starting voice-to-voice pipeline")
            pipeline_start = time.time()

            # Step 1: Speech to Text
            self.logger.info("📝 Step 1: Speech-to-Text conversion")
            if isinstance(audio_input, str):
                stt_result = self.stt.transcribe_audio_file(audio_input)
            else:
                stt_result = self.stt.transcribe_audio_bytes(audio_input)

            transcribed_text = stt_result["text"]
            self.logger.info(f"📄 Transcribed: '{transcribed_text[:100]}...'")

            # Step 2: Text to Speech (if response text provided)
            audio_response = None
            audio_response_size = 0
            
            if response_text:
                self.logger.info("🎵 Step 2: Text-to-Speech conversion")
                audio_response = self.tts.text_to_speech_base64(response_text, language=language)
                audio_response_size = len(audio_response) if audio_response else 0

            pipeline_time = time.time() - pipeline_start

            result = {
                "transcribed_text": transcribed_text,
                "response_text": response_text,
                "audio_response": audio_response,
                "audio_response_size": audio_response_size,
                "input_language": stt_result.get("language", "unknown"),
                "output_language": language,
                "stt_duration": stt_result.get("duration", 0),
                "total_pipeline_duration": pipeline_time,
                "status": "success"
            }

            self.logger.info(f"✅ Voice-to-voice pipeline completed in {pipeline_time:.2f}s")
            return result

        except Exception as e:
            self.logger.error(f"❌ Voice-to-voice pipeline failed: {str(e)}")
            return {
                "transcribed_text": "",
                "response_text": response_text,
                "audio_response": None,
                "audio_response_size": 0,
                "input_language": "unknown",
                "output_language": language,
                "stt_duration": 0,
                "total_pipeline_duration": 0,
                "status": "error",
                "error": str(e)
            }

    def text_to_speech_only(self, text, language="en", output_format="base64"):
        """
        Convert text to speech only

        Args:
            text (str): Text to convert
            language (str): Language code
            output_format (str): "base64", "bytes", or "file"

        Returns:
            Audio in requested format
        """
        try:
            self.logger.info(f"🎵 Converting text to speech: '{text[:50]}...'")
            
            if output_format == "base64":
                return self.tts.text_to_speech_base64(text, language)
            elif output_format == "bytes":
                return self.tts.text_to_speech_bytes(text, language)
            elif output_format == "file":
                return self.tts.text_to_speech_file(text, language=language)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
                
        except Exception as e:
            self.logger.error(f"❌ Text-to-speech conversion failed: {str(e)}")
            raise

    def speech_to_text_only(self, audio_input):
        """
        Convert speech to text only

        Args:
            audio_input: Audio file path or audio bytes

        Returns:
            dict: Transcription results
        """
        try:
            self.logger.info("📝 Converting speech to text")
            
            if isinstance(audio_input, str):
                return self.stt.transcribe_audio_file(audio_input)
            else:
                return self.stt.transcribe_audio_bytes(audio_input)
                
        except Exception as e:
            self.logger.error(f"❌ Speech-to-text conversion failed: {str(e)}")
            raise

    def get_service_info(self):
        """Get information about both services"""
        try:
            stt_info = self.stt.get_model_info() if hasattr(self.stt, 'get_model_info') else {}
            tts_info = self.tts.get_model_info() if hasattr(self.tts, 'get_model_info') else {}
            
            return {
                "stt_service": stt_info,
                "tts_service": tts_info,
                "combined_service": "Ready",
                "capabilities": [
                    "Speech-to-Text",
                    "Text-to-Speech", 
                    "Voice-to-Voice Pipeline"
                ]
            }
        except Exception as e:
            self.logger.error(f"❌ Failed to get service info: {str(e)}")
            return {"error": str(e)}

    def health_check(self):
        """Perform health check on both services"""
        try:
            self.logger.info("🔍 Performing combined speech service health check")
            
            stt_healthy = self.stt.health_check() if hasattr(self.stt, 'health_check') else True
            tts_healthy = self.tts.health_check() if hasattr(self.tts, 'health_check') else True
            
            overall_health = stt_healthy and tts_healthy
            
            health_status = {
                "stt_service": "healthy" if stt_healthy else "unhealthy",
                "tts_service": "healthy" if tts_healthy else "unhealthy",
                "overall_status": "healthy" if overall_health else "unhealthy"
            }
            
            if overall_health:
                self.logger.info("✅ All speech services are healthy")
            else:
                self.logger.warning("⚠️ Some speech services are unhealthy")
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"❌ Speech service health check failed: {str(e)}")
            return {
                "stt_service": "error",
                "tts_service": "error", 
                "overall_status": "error",
                "error": str(e)
            }