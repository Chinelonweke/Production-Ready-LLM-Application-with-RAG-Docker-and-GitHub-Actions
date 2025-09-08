# app/logger_config.py
import logging
import logging.handlers
from datetime import datetime
import os
import sys
from config import Config

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[91m',   # Bright Red
    }
    
    RESET = '\033[0m'  # Reset color
    
    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)
        
        # Get color for the log level
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Add color to the log level only
        colored_level = f"{color}{record.levelname}{self.RESET}"
        
        # Replace the level name with colored version
        formatted_message = original_format.replace(record.levelname, colored_level)
        
        return formatted_message

class WindowsSafeFormatter(logging.Formatter):
    """Windows-safe formatter without emojis"""
    
    def format(self, record):
        # Use simple text instead of emojis for Windows compatibility
        return super().format(record)

class AudioLogger:
    """Specialized logger for audio operations"""
    
    def __init__(self, name="audio_service"):
        self.logger = logging.getLogger(name)
        
    def log_audio_start(self, operation, filename=None):
        if filename:
            self.logger.info(f"[AUDIO] Starting {operation} for file: {filename}")
        else:
            self.logger.info(f"[AUDIO] Starting {operation}")
    
    def log_audio_success(self, operation, duration=None):
        if duration:
            self.logger.info(f"[SUCCESS] {operation} completed successfully in {duration:.2f}s")
        else:
            self.logger.info(f"[SUCCESS] {operation} completed successfully")
    
    def log_audio_error(self, operation, error):
        self.logger.error(f"[ERROR] {operation} failed: {str(error)}")

def is_windows():
    """Check if running on Windows"""
    return sys.platform.startswith('win')

def setup_logging():
    """Set up the logging configuration with colors and file rotation"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Choose formatter based on platform
    if is_windows():
        # Use Windows-safe formatter without emojis
        console_formatter = WindowsSafeFormatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Use colored formatter for Unix systems
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler with rotation (no colors in file)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f'logs/{Config.LOG_FILE}',
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'  # Explicit UTF-8 encoding for file
    )
    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler for errors only
    error_handler = logging.handlers.RotatingFileHandler(
        filename='logs/error.log',
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'  # Explicit UTF-8 encoding for file
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_system_info():
    """Log system startup information - Windows compatible"""
    logger = get_logger("system")
    logger.info("=" * 50)
    logger.info("[STARTUP] RAG Application Starting Up")
    logger.info(f"[INFO] Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"[CONFIG] Log Level: {Config.LOG_LEVEL}")
    logger.info(f"[CONFIG] Vector DB Path: {Config.VECTOR_DB_PATH}")
    logger.info(f"[CONFIG] Whisper Model: {Config.WHISPER_MODEL}")
    
    # Only log TTS model if it exists in config
    if hasattr(Config, 'TTS_MODEL_NAME'):
        logger.info(f"[CONFIG] TTS Model: {Config.TTS_MODEL_NAME}")
    else:
        logger.info("[CONFIG] TTS Model: Google TTS (gTTS)")
    
    logger.info(f"[SYSTEM] Platform: {sys.platform}")
    logger.info(f"[SYSTEM] Python Version: {sys.version.split()[0]}")
    logger.info("=" * 50)

def log_request(func):
    """Decorator to log API requests"""
    def wrapper(*args, **kwargs):
        logger = get_logger("api")
        logger.info(f"[REQUEST] API Request: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"[RESPONSE] API Response: {func.__name__} - Success")
            return result
        except Exception as e:
            logger.error(f"[ERROR] API Error: {func.__name__} - {str(e)}")
            raise
    return wrapper

# Utility functions for different log types
def log_success(logger, message):
    """Log success message in a platform-safe way"""
    logger.info(f"[SUCCESS] {message}")

def log_error(logger, message):
    """Log error message in a platform-safe way"""
    logger.error(f"[ERROR] {message}")

def log_warning(logger, message):
    """Log warning message in a platform-safe way"""
    logger.warning(f"[WARNING] {message}")

def log_info(logger, message):
    """Log info message in a platform-safe way"""
    logger.info(f"[INFO] {message}")

def log_debug(logger, message):
    """Log debug message in a platform-safe way"""
    logger.debug(f"[DEBUG] {message}")