# Enhanced Dockerfile for Production-Ready LLM Application with Audio Processing
FROM python:3.10-slim

# Set metadata
LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Production-Ready LLM Application with RAG, Audio Processing, and Enhanced Logging"
LABEL version="2.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and ML
RUN apt-get update && apt-get install -y \
    # Basic build tools
    build-essential \
    curl \
    wget \
    git \
    # Audio processing dependencies
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    portaudio19-dev \
    libasound2-dev \
    # Additional audio libraries
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    # System monitoring tools
    htop \
    # PDF processing
    poppler-utils \
    # SSL and security
    ca-certificates \
    # Cleanup in same layer to reduce image size
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# Create app user for security (don't run as root)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs \
    /app/vector_db \
    /app/temp_audio \
    /app/static/uploads \
    && chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download required models and data (this will cache them in the image)
RUN python -c "import whisper; whisper.load_model('base')" && \
    python -c "from TTS.api import TTS; TTS('tts_models/en/ljspeech/tacotron2-DDC')" || echo "TTS model download may fail, will retry at runtime"

# Copy application code
COPY . .

# Set proper permissions for the app directory
RUN chown -R appuser:appuser /app && \
    chmod +x /app/app/main.py

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Starting Production RAG Application..."\n\
echo "Checking system resources..."\n\
python -c "import psutil; print(f\"CPU: {psutil.cpu_count()} cores, RAM: {psutil.virtual_memory().total // (1024**3)}GB\")"\n\
echo "Initializing application..."\n\
cd /app\n\
exec python app/main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Set the startup command
CMD ["/app/start.sh"]

# Alternative commands for different environments:
# Development: CMD ["python", "app/main.py"]
# Production with Gunicorn: CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app.main:app"]

# Build arguments for customization
ARG WHISPER_MODEL=base
ARG TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
ARG LOG_LEVEL=INFO

# Set runtime environment variables
ENV WHISPER_MODEL=${WHISPER_MODEL}
ENV TTS_MODEL_NAME=${TTS_MODEL}
ENV LOG_LEVEL=${LOG_LEVEL}
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Volume mounts for persistent data
VOLUME ["/app/logs", "/app/vector_db", "/app/temp_audio"]

# Multi-stage build option (uncomment for smaller production image)
# FROM python:3.10-slim as production
# COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
# COPY --from=builder /app /app
# COPY --from=builder /usr/bin/ffmpeg /usr/bin/ffmpeg
# USER appuser
# CMD ["/app/start.sh"]