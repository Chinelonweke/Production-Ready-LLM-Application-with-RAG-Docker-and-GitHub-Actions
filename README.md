# 🚀 Production-Ready LLM Application with RAG, Audio, and Enhanced Logging

A comprehensive, production-ready application that combines Retrieval Augmented Generation (RAG) with advanced audio processing capabilities, colorful logging, and cloud integration. **Now with FREE HuggingFace embeddings!**

## ✨ Features

### 🧠 Core AI Capabilities
- **RAG System**: Advanced document processing and retrieval
- **Groq LLM**: Fast LLM inference for responses
- **FREE Embeddings**: HuggingFace `all-MiniLM-L6-v2` (no API costs!)
- **Vector Database**: ChromaDB for semantic search
- **Smart Chunking**: Intelligent document splitting

### 🎵 Audio Processing
- **Speech-to-Text**: OpenAI Whisper integration
- **Text-to-Speech**: Coqui TTS for realistic voice synthesis
- **Real-time Audio**: Voice conversations with AI
- **Multiple Formats**: Support for WAV, MP3, FLAC, M4A, OGG

### 📊 Monitoring & Logging
- **Colorful Logs**: Custom colored console output
- **Structured Logging**: JSON logs with rotation
- **Health Checks**: Comprehensive system monitoring
- **Performance Metrics**: Response time tracking

### ☁️ Cloud Integration
- **AWS S3**: Document storage and management
- **Docker Ready**: Production containerization
- **CI/CD Pipeline**: GitHub Actions automation
- **Auto-scaling**: Production deployment ready

## 🏗️ Project Structure

```
project/
├── app/
│   ├── main.py                 # Main Flask application
│   ├── config.py              # Configuration management
│   ├── logger_config.py       # Enhanced logging system
│   ├── models/
│   │   ├── __init__.py
│   │   └── vector_store.py     # Vector database (FREE embeddings!)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── storage_service.py  # AWS S3 integration
│   │   ├── llm_service.py      # Groq LLM interactions
│   │   ├── audio_service.py    # Whisper STT
│   │   └── speech_service.py   # Coqui TTS
│   ├── static/
│   │   ├── style.css          # Enhanced UI styles
│   │   └── js/
│   │       └── audio.js       # Audio functionality
│   └── templates/
│       └── index.html         # Main web interface
├── requirements.txt           # Python dependencies
├── Dockerfile                # Container configuration
├── .env.template             # Environment variables template
├── .github/workflows/
│   └── workflow.yml          # CI/CD pipeline
└── README.md                 # This file
```

## 🛠️ Installation & Setup

### Prerequisites

Before starting, ensure you have:
- Python 3.9+ installed
- Docker (for containerization)
- Git
- AWS Account (for S3 storage)
- Groq API Account (FREE tier available!)

### Step 1: Clone the Repository

```bash
git clone <https://github.com/Chinelonweke/Production-Ready-LLM-Application-with-RAG-Docker-and-GitHub-Actions>
cd rag-application
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    portaudio19-dev \
    build-essential
```

#### macOS:
```bash
brew install ffmpeg portaudio
```

#### Windows:
- Install ffmpeg from https://ffmpeg.org/download.html
- Add ffmpeg to your PATH

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Copy environment template
cp .env.template .env

# Edit the .env file with your credentials
nano .env  # or use your preferred editor
```

Fill in the following required variables:

```bash
# Required API Keys
GROQ_API_KEY=your_groq_api_key_here

# AWS Configuration (for document storage)
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_BUCKET_NAME=your_s3_bucket_name
AWS_REGION=us-east-1

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=INFO
```

**🎉 Note**: 
- ✅ **OpenAI API key is NO LONGER REQUIRED!** 
- ✅ **We use FREE HuggingFace embeddings: `all-MiniLM-L6-v2`**
- ✅ **No configuration needed - works out of the box!**

### Step 6: Set Up AWS S3 Bucket

1. **Create S3 Bucket:**
   ```bash
   aws s3 mb s3://your-bucket-name
   ```

2. **Set Bucket Policy (Optional):**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::YOUR-ACCOUNT-ID:user/YOUR-USERNAME"
         },
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::your-bucket-name/*"
       }
     ]
   }
   ```

### Step 7: Initialize the Application

```bash
# Create necessary directories
mkdir -p logs vector_db temp_audio

# Initialize vector database (first run)
python -c "from app.models.vector_store import VectorStore; VectorStore('vector_db')"
```

## 🚀 Running the Application

### Development Mode

```bash
python app/main.py
```

The application will start on `http://localhost:8080`

### Production Mode with Docker

```bash
# Build the Docker image
docker build -t rag-app:latest .

# Run the container
docker run -d \
  --name rag-app \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/vector_db:/app/vector_db \
  -v $(pwd)/temp_audio:/app/temp_audio \
  rag-app:latest
```

## 📖 API Documentation

### Health Check
```bash
GET /health
```
Returns system health status and service availability.

### Document Upload
```bash
POST /upload
Content-Type: multipart/form-data

# Upload a PDF or TXT file
curl -X POST -F "file=@document.pdf" http://localhost:8080/upload
```

### Text Query
```bash
POST /query
Content-Type: application/json

{
  "question": "What is the main topic of the document?",
  "include_sources": true
}
```

### Audio Transcription
```bash
POST /audio/transcribe
Content-Type: multipart/form-data

# Upload audio file for transcription
curl -X POST -F "audio=@recording.wav" http://localhost:8080/audio/transcribe
```

### Text-to-Speech
```bash
POST /audio/synthesize
Content-Type: application/json

{
  "text": "Hello, this is a test message",
  "language": "en",
  "format": "base64"
}
```

### Voice-to-Voice Conversation
```bash
POST /audio/voice-to-voice
Content-Type: multipart/form-data

# Complete voice conversation pipeline
curl -X POST \
  -F "audio=@question.wav" \
  -F "language=en" \
  -F "include_sources=true" \
  http://localhost:8080/audio/voice-to-voice
```

## 🎛️ Web Interface Usage

### 1. **Document Upload**
- Click "Choose Files" in the upload section
- Select PDF or TXT files
- Click "Upload Documents"
- Wait for processing confirmation

### 2. **Text Queries**
- Enter your question in the text area
- Click "Ask Question"
- View AI response with sources
- Use "Speak Response" for audio playback

### 3. **Voice Recording**
- Click "Start Recording" to record your question
- Click "Stop Recording" when finished
- Click "Play Recording" to review
- Question text will appear automatically

### 4. **Audio File Upload**
- Choose an audio file (WAV, MP3, etc.)
- Click "Transcribe Audio"
- Transcribed text appears in the question field

### 5. **Voice Conversation**
- Click "Start Voice Conversation"
- Speak your question
- Click "Click to Stop & Process"
- Receive both text and audio response

## 🔧 Configuration Options

### FREE Embedding Model
```python
# In app/models/vector_store.py (line 28-29)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```

**Benefits:**
- ✅ **$0 cost** - Completely free
- ✅ **No API key** needed
- ✅ **Privacy** - Runs locally
- ✅ **Good quality** - Perfect for most use cases
- ✅ **Fast** - Optimized for speed

### Audio Settings
```python
# In config.py
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
TTS_MODEL_NAME = "tts_models/en/ljspeech/tacotron2-DDC"
TTS_VOICE_SPEED = 1.0
MAX_AUDIO_FILE_SIZE = 16 * 1024 * 1024  # 16MB
```

### Document Processing
```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

## 🚀 Deployment

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  rag-app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./vector_db:/app/vector_db
      - ./temp_audio:/app/temp_audio
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### GitHub Actions Deployment

The included GitHub Actions workflow automatically:
1. **Code Quality Checks**: Linting, formatting, security scans
2. **Testing**: Unit tests across Python versions
3. **Security Scanning**: Container vulnerability assessment
4. **AWS ECR**: Automated image building and pushing
5. **Production Deployment**: Zero-downtime deployments

Configure these secrets in your GitHub repository:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY_NAME`
- `GROQ_API_KEY`
- `AWS_BUCKET_NAME`

## 📊 Monitoring & Troubleshooting

### Viewing Logs
```bash
# Real-time logs
tail -f logs/app.log

# Error logs only
tail -f logs/error.log

# Docker logs
docker logs -f rag-app
```

### Health Monitoring
```bash
# Check system health
curl http://localhost:8080/health

# Get service information
curl http://localhost:8080/services/info

# Audio service info
curl http://localhost:8080/audio/info
```

### Common Issues

#### 1. **Audio Dependencies Missing**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsndfile1 portaudio19-dev

# macOS
brew install ffmpeg portaudio
```

#### 2. **Model Download Failures**
```bash
# Manually download Whisper model
python -c "import whisper; whisper.load_model('base')"

# Manually download TTS model
python -c "from TTS.api import TTS; TTS('tts_models/en/ljspeech/tacotron2-DDC')"

# Manually download embedding model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### 3. **Memory Issues**
- Reduce Whisper model size to "tiny" or "small"
- Increase Docker memory allocation
- Monitor memory usage with logs

#### 4. **AWS Connection Issues**
- Verify AWS credentials
- Check S3 bucket permissions
- Confirm AWS region settings

## 🔐 Security Considerations

### Production Checklist
- [ ] Use strong, unique SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Disable debug mode
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Monitor application logs
- [ ] Use least-privilege AWS policies

### Environment Security
```bash
# Secure environment file permissions
chmod 600 .env

# Use AWS IAM roles instead of access keys when possible
# Rotate API keys regularly
# Monitor AWS CloudTrail for unusual activity
```

## 🧪 Testing

### Run Tests
```bash
# Unit tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=html

# Integration tests
python -m pytest tests/integration/ -v
```

### Manual Testing
```bash
# Test API endpoints
curl -X GET http://localhost:8080/health
curl -X POST -F "file=@test.pdf" http://localhost:8080/upload
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"test"}' http://localhost:8080/query
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run code quality checks
5. Submit a pull request

### Code Style
```bash
# Format code
black app/
isort app/

# Lint code
flake8 app/

# Security check
bandit -r app/
```

## 💰 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| **Embeddings** | **FREE** ✅ | HuggingFace local model |
| **Groq LLM** | **FREE tier** ✅ | Then $0.27/1M tokens |
| **AWS S3** | ~$0.023/GB | Document storage |
| **Whisper STT** | **FREE** ✅ | Local processing |
| **Coqui TTS** | **FREE** ✅ | Local processing |

**Monthly cost for typical usage: $0-5** 🎉

## 📚 Additional Resources

- [Whisper Documentation](https://github.com/openai/whisper)
- [Coqui TTS Documentation](https://docs.coqui.ai/)
- [LangChain Documentation](https://docs.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [HuggingFace Sentence Transformers](https://www.sbert.net/)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Support

For issues and questions:
1. Check existing GitHub issues
2. Review troubleshooting section
3. Create a new issue with:
   - Python version
   - Operating system
   - Error logs
   - Steps to reproduce

---

**Happy Building! 🚀**

**Key Features:**
- ✅ **FREE embeddings** with HuggingFace
- ✅ **Groq LLM** for fast responses  
- ✅ **Complete audio pipeline** (STT + TTS)
- ✅ **Production ready** with Docker & CI/CD
- ✅ **Enhanced logging** with colors
- ✅ **Zero ongoing costs** for embeddings