# app/main.py
from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import time
from datetime import datetime

# Import configurations and logging
from config import Config
from logger_config import setup_logging, get_logger, log_system_info

# Import services
from models.vector_store import VectorStore
from services.storage_service import S3Storage
from services.llm_service import LLMService
from services.audio_service import WhisperSTTService
from services.speech_service import GoogleTTSService, SpeechService

# Import document processing
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Setup logging
setup_logging()
logger = get_logger("main")

# Log system startup info
log_system_info()

# Create necessary directories
Config.create_directories()

# Initialize services
logger.info("Initializing services...")

try:
    # Vector store
    vector_store = VectorStore(Config.VECTOR_DB_PATH)
    logger.info("Vector store initialized")
    
    # Storage service (with error handling for S3)
    storage_service = None
    try:
        storage_service = S3Storage()
        logger.info("S3 storage service initialized")
    except Exception as storage_error:
        logger.warning(f"S3 storage service failed: {str(storage_error)}")
        logger.info("Continuing with local file storage only")
        storage_service = None
    
    # LLM service
    llm_service = LLMService(vector_store)
    logger.info("LLM service initialized")
    
    # Audio services
    stt_service = WhisperSTTService()
    logger.info("STT service initialized")
    
    tts_service = GoogleTTSService()
    logger.info("TTS service initialized")
    
    # Combined speech service
    speech_service = SpeechService(stt_service, tts_service)
    logger.info("Speech service initialized")
    
    logger.info("All available services initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize core services: {str(e)}")
    raise

# Routes
@app.route('/')
def index():
    """Main page"""
    logger.info("Serving main page")
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Performing health check")
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "services": {
            "vector_store": vector_store.health_check(),
            "storage": storage_service.health_check() if storage_service else False,
            "llm": llm_service.health_check() if hasattr(llm_service, 'health_check') else True,
            "stt": stt_service.health_check() if hasattr(stt_service, 'health_check') else True,
            "tts": tts_service.health_check() if hasattr(tts_service, 'health_check') else True
        },
        "storage_note": "S3 disabled - using local storage only" if not storage_service else "S3 storage active"
    }
    
    # Overall health (storage failure doesn't affect overall health)
    core_services = ["vector_store", "llm", "stt", "tts"]
    core_healthy = all(health_status["services"][service] for service in core_services)
    health_status["status"] = "healthy" if core_healthy else "degraded"
    
    return jsonify(health_status), 200 if core_healthy else 503

def process_document(file):
    """Process document based on file type and return text chunks"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        logger.info(f"Processing document: {file.filename}")
        
        # Save file temporarily
        file.save(temp_path)
        
        # Process based on file type
        if file.filename.lower().endswith('.pdf'):
            loader = PyPDFLoader(temp_path)
            documents = loader.load()
        elif file.filename.lower().endswith('.txt'):
            loader = TextLoader(temp_path, encoding='utf-8')
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")

        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        text_chunks = text_splitter.split_documents(documents)
        
        logger.info(f"Document processed into {len(text_chunks)} chunks")
        return text_chunks
        
    except Exception as e:
        logger.error(f"Error processing document {file.filename}: {str(e)}")
        raise
        
    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup error: {cleanup_error}")

@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process document"""
    logger.info("Document upload request received")
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check file extension
        allowed_extensions = ['.txt', '.pdf']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            return jsonify({
                'error': f'Only {", ".join(allowed_extensions)} files are supported'
            }), 400

        # Process the document
        text_chunks = process_document(file)

        # Try to upload to S3 if available, otherwise save locally
        upload_result = {"success": True, "storage": "local", "message": "File processed successfully"}
        
        if storage_service:
            try:
                file.seek(0)  # Reset file pointer
                upload_result = storage_service.upload_file(file, file.filename)
                upload_result["storage"] = "s3"
            except Exception as s3_error:
                logger.warning(f"S3 upload failed, using local storage: {s3_error}")
                upload_result["storage"] = "local"
                upload_result["s3_error"] = str(s3_error)
        
        # Add to vector store
        if not vector_store.add_documents(text_chunks):
            return jsonify({'error': 'Failed to add documents to vector store'}), 500

        logger.info(f"Upload successful: {file.filename}")
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'filename': file.filename,
            'chunks_processed': len(text_chunks),
            'storage_info': upload_result
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/query', methods=['POST'])
def query():
    """Process text query"""
    logger.info("Text query request received")
    try:
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        if not question.strip():
            return jsonify({'error': 'Question cannot be empty'}), 400
            
        include_sources = data.get('include_sources', True)
        
        logger.info(f"Processing query: {question[:50]}...")
        response = llm_service.get_response(question, include_sources=include_sources)
        
        logger.info("Query processed successfully")
        return jsonify({
            'success': True,
            **response
        })

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        return jsonify({'error': f'Query failed: {str(e)}'}), 500

@app.route('/audio/transcribe', methods=['POST'])
def transcribe_audio():
    """Transcribe audio to text using Whisper"""
    logger.info("Audio transcription request received")
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Check file extension
        file_ext = audio_file.filename.lower().split('.')[-1]
        if file_ext not in Config.ALLOWED_AUDIO_EXTENSIONS:
            return jsonify({
                'error': f'Unsupported audio format. Supported: {", ".join(Config.ALLOWED_AUDIO_EXTENSIONS)}'
            }), 400
        
        # Check file size
        audio_file.seek(0, 2)  # Seek to end
        file_size = audio_file.tell()
        audio_file.seek(0)  # Reset
        
        if file_size > Config.MAX_AUDIO_FILE_SIZE:
            return jsonify({'error': 'Audio file too large. Maximum size: 16MB'}), 400
        
        # Transcribe audio
        result = stt_service.transcribe_audio_bytes(audio_file.read(), audio_file.filename)
        
        logger.info("Audio transcription completed successfully")
        return jsonify({
            'success': True,
            'transcription': result['text'],
            'language': result['language'],
            'duration': result['duration'],
            'segments': result.get('segments', [])
        })

    except Exception as e:
        logger.error(f"Audio transcription error: {str(e)}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500

@app.route('/audio/synthesize', methods=['POST'])
def synthesize_speech():
    """Convert text to speech using Google TTS"""
    logger.info("Speech synthesis request received")
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({'error': 'Text cannot be empty'}), 400
            
        language = data.get('language', 'en')
        format_type = data.get('format', 'base64')  # 'base64' or 'file'
        
        # Validate language
        available_languages = tts_service.get_available_languages()
        if language not in available_languages:
            return jsonify({
                'error': f'Unsupported language: {language}. Available: {list(available_languages.keys())}'
            }), 400
        
        if format_type == 'base64':
            # Return base64 encoded audio
            audio_base64 = tts_service.text_to_speech_base64(text, language=language)
            
            logger.info("Speech synthesis completed successfully")
            return jsonify({
                'success': True,
                'audio_data': audio_base64,
                'format': 'base64',
                'text': text,
                'language': language
            })
        
        elif format_type == 'file':
            # Return audio file
            audio_path = tts_service.text_to_speech_file(text, language=language)
            
            return send_file(
                audio_path,
                as_attachment=True,
                download_name=f'speech_{int(time.time())}.mp3',  # gTTS outputs MP3
                mimetype='audio/mpeg'
            )
        
        else:
            return jsonify({'error': 'Invalid format. Use "base64" or "file"'}), 400

    except Exception as e:
        logger.error(f"Speech synthesis error: {str(e)}")
        return jsonify({'error': f'Speech synthesis failed: {str(e)}'}), 500

@app.route('/audio/voice-to-voice', methods=['POST'])
def voice_to_voice():
    """Complete voice-to-voice pipeline: STT -> LLM -> TTS"""
    logger.info("Voice-to-voice pipeline request received")
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
            
        language = request.form.get('language', 'en')
        include_sources = request.form.get('include_sources', 'true').lower() == 'true'
        
        # Step 1: Transcribe audio
        logger.info("Starting voice-to-voice pipeline")
        start_time = time.time()
        
        transcription_result = stt_service.transcribe_audio_bytes(audio_file.read(), audio_file.filename)
        user_text = transcription_result['text']
        
        if not user_text.strip():
            return jsonify({'error': 'No speech detected in audio'}), 400
        
        # Step 2: Get LLM response
        logger.info(f"Processing question: {user_text[:50]}...")
        llm_response = llm_service.get_response(user_text, include_sources=include_sources)
        response_text = llm_response['answer']
        
        # Step 3: Convert response to speech
        logger.info("Converting response to speech")
        audio_response = tts_service.text_to_speech_base64(response_text, language=language)
        
        total_time = time.time() - start_time
        
        logger.info("Voice-to-voice pipeline completed successfully")
        return jsonify({
            'success': True,
            'user_speech': user_text,
            'ai_response_text': response_text,
            'ai_response_audio': audio_response,
            'transcription_language': transcription_result['language'],
            'output_language': language,
            'processing_time': {
                'transcription': transcription_result['duration'],
                'llm_response': llm_response.get('response_time', 0),
                'total_pipeline': total_time
            },
            'sources': llm_response.get('sources', []) if include_sources else []
        })

    except Exception as e:
        logger.error(f"Voice-to-voice error: {str(e)}")
        return jsonify({'error': f'Voice-to-voice pipeline failed: {str(e)}'}), 500

@app.route('/audio/info', methods=['GET'])
def audio_info():
    """Get audio service information"""
    try:
        stt_info = stt_service.get_model_info() if hasattr(stt_service, 'get_model_info') else {}
        tts_info = tts_service.get_model_info() if hasattr(tts_service, 'get_model_info') else {}
        
        return jsonify({
            'success': True,
            'stt': stt_info,
            'tts': tts_info,
            'supported_audio_formats': list(Config.ALLOWED_AUDIO_EXTENSIONS),
            'max_file_size': Config.MAX_AUDIO_FILE_SIZE,
            'max_file_size_mb': Config.MAX_AUDIO_FILE_SIZE / (1024 * 1024)
        })
    
    except Exception as e:
        logger.error(f"Error getting audio info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/services/info', methods=['GET'])
def services_info():
    """Get information about all services"""
    try:
        return jsonify({
            'success': True,
            'vector_store': vector_store.get_collection_info(),
            'storage': {
                "type": "S3" if storage_service else "Local",
                "status": "active" if storage_service else "disabled",
                "note": "Cloud storage available" if storage_service else "Using local file storage only"
            },
            'llm': llm_service.get_model_info() if hasattr(llm_service, 'get_model_info') else {},
            'audio': {
                'stt': stt_service.get_model_info() if hasattr(stt_service, 'get_model_info') else {},
                'tts': tts_service.get_model_info() if hasattr(tts_service, 'get_model_info') else {}
            }
        })
    except Exception as e:
        logger.error(f"Error getting services info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tts/languages', methods=['GET'])
def get_tts_languages():
    """Get available TTS languages"""
    try:
        languages = tts_service.get_available_languages()
        return jsonify({
            'success': True,
            'languages': languages,
            'default_language': 'en'
        })
    except Exception as e:
        logger.error(f"Error getting TTS languages: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    logger.error("File too large error")
    return jsonify({'error': 'File too large'}), 413

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application")
        logger.info(f"Running on http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        logger.info("Storage: S3" if storage_service else "Storage: Local files only")
        
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise