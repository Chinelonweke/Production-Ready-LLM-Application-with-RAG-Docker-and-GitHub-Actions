#!/bin/bash

# setup.sh - Quick Setup Script for Production-Ready RAG Application
# This script automates the initial setup process with FREE HuggingFace embeddings

set -e  # Exit on any error

echo "🚀 Setting up Production-Ready RAG Application with Audio Features"
echo "================================================================="
echo "🎉 Now with FREE HuggingFace Embeddings - No OpenAI API key needed!"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_status "Detected OS: $OS"

# Step 1: Check Python version
print_step "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 9 ]]; then
        print_status "Python $PYTHON_VERSION is compatible"
        PYTHON_CMD="python3"
    else
        print_error "Python 3.9+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Step 2: Install system dependencies
print_step "2. Installing system dependencies..."

if [[ $OS == "linux" ]]; then
    print_status "Installing Linux dependencies..."
    
    # Check if running Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            ffmpeg \
            libsndfile1 \
            libsndfile1-dev \
            portaudio19-dev \
            build-essential \
            curl \
            git
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        sudo yum install -y \
            ffmpeg \
            libsndfile-devel \
            portaudio-devel \
            gcc \
            gcc-c++ \
            make \
            curl \
            git
    else
        print_warning "Unknown Linux distribution. Please install audio dependencies manually."
    fi
    
elif [[ $OS == "macos" ]]; then
    print_status "Installing macOS dependencies..."
    
    if command -v brew &> /dev/null; then
        brew install ffmpeg portaudio
    else
        print_error "Homebrew is required on macOS. Install from https://brew.sh/"
        exit 1
    fi
    
elif [[ $OS == "windows" ]]; then
    print_warning "Windows detected. Please ensure ffmpeg is installed and in PATH."
    print_warning "Download from: https://ffmpeg.org/download.html"
fi

# Step 3: Create virtual environment
print_step "3. Creating Python virtual environment..."

if [[ ! -d "venv" ]]; then
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
if [[ $OS == "windows" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

print_status "Virtual environment activated"

# Step 4: Upgrade pip and install dependencies
print_step "4. Installing Python dependencies..."

pip install --upgrade pip setuptools wheel
print_status "Upgraded pip, setuptools, and wheel"

print_status "Installing application dependencies (this may take a while)..."
pip install -r requirements.txt

# Step 5: Download AI models
print_step "5. Downloading AI models..."

print_status "Downloading FREE HuggingFace embedding model (all-MiniLM-L6-v2)..."
$PYTHON_CMD -c "
from sentence_transformers import SentenceTransformer
print('📦 Downloading all-MiniLM-L6-v2 embedding model...')
model = SentenceTransformer('all-MiniLM-L6-v2')
print('✅ Embedding model downloaded successfully!')
print('💰 Cost: $0 (FREE)')
print('🏠 Stored locally - no API calls needed')
" || print_warning "Embedding model download failed, will retry at runtime"

print_status "Downloading Whisper base model..."
$PYTHON_CMD -c "import whisper; whisper.load_model('base')" || print_warning "Whisper model download failed, will retry at runtime"

print_status "Downloading TTS model..."
$PYTHON_CMD -c "from TTS.api import TTS; TTS('tts_models/en/ljspeech/tacotron2-DDC')" || print_warning "TTS model download failed, will retry at runtime"

# Step 6: Set up environment file
print_step "6. Setting up environment configuration..."

if [[ ! -f ".env" ]]; then
    cp .env.template .env
    print_status "Environment template copied to .env"
    print_warning "Please edit .env file with your API keys and AWS credentials"
else
    print_status ".env file already exists"
fi

# Step 7: Create necessary directories
print_step "7. Creating application directories..."

mkdir -p logs vector_db temp_audio static/uploads
print_status "Created application directories"

# Step 8: Set up basic configuration
print_step "8. Running initial configuration..."

# Test imports
$PYTHON_CMD -c "
try:
    from app.config import Config
    from app.logger_config import setup_logging
    from langchain.embeddings import HuggingFaceEmbeddings
    
    # Test the FREE embedding
    print('🧪 Testing FREE HuggingFace embeddings...')
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
    test_embedding = embeddings.embed_query('Hello world')
    print(f'✅ Embedding test successful! Dimension: {len(test_embedding)}')
    print('💰 Cost: $0 (completely free)')
    print('🔑 API Key: Not needed')
    print('🏠 Processing: Local (private)')
    
    print('✅ Core imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

# Step 9: Create a test script
print_step "9. Creating test script..."

cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify the application setup with FREE embeddings
"""
import sys
import os

def test_imports():
    """Test core imports"""
    try:
        from app.config import Config
        from app.logger_config import setup_logging, get_logger
        from langchain.embeddings import HuggingFaceEmbeddings
        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_embeddings():
    """Test FREE HuggingFace embeddings"""
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        print("🧪 Testing FREE HuggingFace embeddings...")
        
        # Test the exact syntax used in the application
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Test embedding a simple query
        test_text = "This is a test embedding"
        result = embeddings.embed_query(test_text)
        
        print(f"✅ Embedding successful!")
        print(f"📊 Dimensions: {len(result)}")
        print(f"💰 Cost: $0 (FREE)")
        print(f"🔑 API Key: Not needed")
        print(f"🏠 Processing: Local")
        
        return True
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False

def test_directories():
    """Test required directories"""
    required_dirs = ['logs', 'vector_db', 'temp_audio']
    all_exist = True
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ Directory '{dir_name}' exists")
        else:
            print(f"❌ Directory '{dir_name}' missing")
            all_exist = False
    
    return all_exist

def test_environment():
    """Test environment configuration"""
    if os.path.exists('.env'):
        print("✅ Environment file exists")
        
        # Check if it's still the template
        with open('.env', 'r') as f:
            content = f.read()
            if 'your_groq_api_key_here' in content:
                print("⚠️  Please update .env with your actual Groq API key")
                print("🎉 Note: OpenAI API key is NO LONGER REQUIRED!")
            else:
                print("✅ Environment file appears to be configured")
        return True
    else:
        print("❌ Environment file missing")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing application setup with FREE embeddings...")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("FREE Embeddings", test_embeddings),
        ("Directories", test_directories),
        ("Environment", test_environment)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}:")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! Setup appears successful.")
        print("\n📝 Next steps:")
        print("1. Edit .env file with your Groq API key (OpenAI not needed!)")
        print("2. Add your AWS credentials for S3 storage")
        print("3. Run: python app/main.py")
        print("4. Open: http://localhost:8080")
        print("\n💰 Embedding cost: $0 (FREE HuggingFace model)")
        print("🔑 No OpenAI API key required for embeddings!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x test_setup.py

# Step 10: Run setup test
print_step "10. Running setup verification..."
$PYTHON_CMD test_setup.py

# Final instructions
echo ""
echo "🎉 Setup completed successfully!"
echo "================================================================="
echo ""
echo "📝 Next Steps:"
echo "1. Edit the .env file with your actual API keys:"
echo "   nano .env"
echo ""
echo "2. Required API keys:"
echo "   - GROQ_API_KEY (get from https://console.groq.com/keys)"
echo "   - AWS credentials for S3 storage"
echo ""
echo "   🎉 OpenAI API key is NO LONGER REQUIRED!"
echo "   📦 We use FREE HuggingFace embeddings: all-MiniLM-L6-v2"
echo "   ✅ No configuration needed - works out of the box!"
echo ""
echo "3. Start the application:"
echo "   source venv/bin/activate  # if not already activated"
echo "   python app/main.py"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8080"
echo ""
echo "🎯 Embedding Features:"
echo "   💰 Cost: $0 (completely FREE)"
echo "   🔑 API Key: Not needed"
echo "   🏠 Privacy: Full (local processing)"
echo "   ⚡ Speed: Fast"
echo "   👍 Quality: Good for most use cases"
echo ""
echo "🔧 Troubleshooting:"
echo "- Run 'python test_setup.py' to verify setup"
echo "- Check logs in the 'logs/' directory"
echo "- Review README.md for detailed documentation"
echo ""
echo "Happy building! 🚀"