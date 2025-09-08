# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    # OpenAI API key is now optional (only needed if you want to use OpenAI embeddings)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
    
    # AWS Configuration
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Vector Database
    VECTOR_DB_PATH = 'vector_db'
    
    # Audio Configuration
    AUDIO_UPLOAD_FOLDER = 'temp_audio'
    MAX_AUDIO_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg'}
    
    # Speech Configuration
    WHISPER_MODEL = 'base'  # base, small, medium, large
    
    # Google TTS Configuration (Updated from Coqui TTS)
    DEFAULT_TTS_LANGUAGE = 'en'  # Default language for Google TTS
    TTS_VOICE_SPEED = 1.0  # Not used by gTTS but kept for compatibility
    
    # Available TTS languages for Google TTS
    AVAILABLE_TTS_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese (Mandarin)',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'no': 'Norwegian'
    }
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))  # Changed from 8080 to 5000 (standard Flask)
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Document Processing
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1000))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    
    # Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    
    # Environment Settings
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 10))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
    
    # Security Settings (for production)
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    @staticmethod
    def create_directories():
        """Create necessary directories if they don't exist"""
        directories = [
            Config.VECTOR_DB_PATH,
            Config.AUDIO_UPLOAD_FOLDER,
            'logs',
            'temp'
        ]
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create directory {directory}: {e}")
    
    @staticmethod
    def validate_config():
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Check required directories
        if not os.path.exists(Config.VECTOR_DB_PATH):
            try:
                os.makedirs(Config.VECTOR_DB_PATH, exist_ok=True)
                warnings.append(f"Created missing directory: {Config.VECTOR_DB_PATH}")
            except Exception as e:
                errors.append(f"Cannot create vector DB directory: {e}")
        
        # Check audio settings
        if Config.MAX_AUDIO_FILE_SIZE > 50 * 1024 * 1024:  # 50MB
            warnings.append("Audio file size limit is very high (>50MB)")
        
        # Check Flask settings
        if Config.FLASK_DEBUG and Config.ENVIRONMENT == 'production':
            warnings.append("Debug mode is enabled in production environment")
        
        # Check API keys (optional warnings)
        if not Config.GROQ_API_KEY:
            warnings.append("GROQ_API_KEY not set - LLM functionality may be limited")
        
        if not Config.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY not set - Will use free embeddings")
        
        return errors, warnings
    
    @staticmethod
    def get_service_info():
        """Get information about configured services"""
        return {
            "vector_db": {
                "path": Config.VECTOR_DB_PATH,
                "embedding_model": Config.EMBEDDING_MODEL,
                "cost": "Free"
            },
            "tts": {
                "engine": "Google TTS (gTTS)",
                "default_language": Config.DEFAULT_TTS_LANGUAGE,
                "available_languages": len(Config.AVAILABLE_TTS_LANGUAGES),
                "cost": "Free"
            },
            "stt": {
                "engine": "OpenAI Whisper",
                "model": Config.WHISPER_MODEL,
                "cost": "Free"
            },
            "web_framework": {
                "engine": "Flask",
                "host": Config.FLASK_HOST,
                "port": Config.FLASK_PORT,
                "debug": Config.FLASK_DEBUG
            },
            "environment": Config.ENVIRONMENT,
            "total_cost": "Free (all services are free)"
        }
    
    @staticmethod
    def print_config_summary():
        """Print a summary of the current configuration"""
        print("=" * 50)
        print("APPLICATION CONFIGURATION SUMMARY")
        print("=" * 50)
        print(f"Environment: {Config.ENVIRONMENT}")
        print(f"Vector DB Path: {Config.VECTOR_DB_PATH}")
        print(f"Flask Host: {Config.FLASK_HOST}:{Config.FLASK_PORT}")
        print(f"Debug Mode: {Config.FLASK_DEBUG}")
        print(f"Log Level: {Config.LOG_LEVEL}")
        print(f"Whisper Model: {Config.WHISPER_MODEL}")
        print(f"Default TTS Language: {Config.DEFAULT_TTS_LANGUAGE}")
        print(f"Embedding Model: {Config.EMBEDDING_MODEL}")
        print("=" * 50)
        
        # Validate and show any issues
        errors, warnings = Config.validate_config()
        
        if errors:
            print("CONFIGURATION ERRORS:")
            for error in errors:
                print(f"  [ERROR] {error}")
        
        if warnings:
            print("CONFIGURATION WARNINGS:")
            for warning in warnings:
                print(f"  [WARNING] {warning}")
        
        if not errors and not warnings:
            print("[SUCCESS] Configuration validation passed")
        
        print("=" * 50)