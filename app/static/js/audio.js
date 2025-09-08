// static/js/audio.js - Audio functionality for the RAG application

class AudioManager {
    constructor() {
        this.mediaRecorder = null;
        this.recordedBlobs = [];
        this.isRecording = false;
        this.stream = null;
        this.audioContext = null;
        
        this.initializeAudio();
    }

    async initializeAudio() {
        try {
            // Check if browser supports audio recording
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                console.warn('Audio recording not supported in this browser');
                this.disableAudioFeatures();
                return;
            }

            // Initialize audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio system initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            this.disableAudioFeatures();
        }
    }

    disableAudioFeatures() {
        const audioElements = [
            'start-recording', 
            'voice-to-voice',
            'audio-upload-form'
        ];
        
        audioElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.disabled = true;
                element.title = 'Audio features not available in this browser';
            }
        });
    }

    async startRecording() {
        try {
            if (this.isRecording) {
                console.warn('Recording already in progress');
                return;
            }

            // Request microphone access
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });

            // Create media recorder
            this.mediaRecorder = new MediaRecorder(this.stream, {
                mimeType: this.getSupportedMimeType()
            });

            this.recordedBlobs = [];

            // Set up event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    this.recordedBlobs.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                console.log('Recording stopped');
                this.updateRecordingUI(false);
                this.enablePlayback();
            };

            this.mediaRecorder.onerror = (event) => {
                console.error('Recording error:', event.error);
                this.stopRecording();
                this.showRecordingStatus('Recording failed', 'error');
            };

            // Start recording
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            this.updateRecordingUI(true);
            this.showRecordingStatus('Recording... Click stop when finished', 'info');

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showRecordingStatus('Failed to access microphone', 'error');
        }
    }

    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            return;
        }

        this.mediaRecorder.stop();
        this.isRecording = false;

        // Stop all tracks to release microphone
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        this.showRecordingStatus('Recording completed', 'success');
    }

    getSupportedMimeType() {
        const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/mp4',
            'audio/wav'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'audio/webm'; // fallback
    }

    updateRecordingUI(isRecording) {
        const startBtn = document.getElementById('start-recording');
        const stopBtn = document.getElementById('stop-recording');

        if (startBtn && stopBtn) {
            startBtn.disabled = isRecording;
            stopBtn.disabled = !isRecording;
            
            if (isRecording) {
                startBtn.innerHTML = '<i class="fas fa-microphone"></i> Recording...';
                startBtn.classList.add('recording');
            } else {
                startBtn.innerHTML = '<i class="fas fa-microphone"></i> Start Recording';
                startBtn.classList.remove('recording');
            }
        }
    }

    enablePlayback() {
        const playBtn = document.getElementById('play-recording');
        if (playBtn && this.recordedBlobs.length > 0) {
            playBtn.disabled = false;
        }
    }

    playRecording() {
        if (this.recordedBlobs.length === 0) {
            this.showRecordingStatus('No recording available', 'warning');
            return;
        }

        const blob = new Blob(this.recordedBlobs, { type: 'audio/webm' });
        const audioUrl = URL.createObjectURL(blob);
        
        const audio = document.getElementById('recorded-audio');
        if (audio) {
            audio.src = audioUrl;
            audio.style.display = 'block';
            audio.play();
            
            // Clean up URL when done
            audio.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
            });
        }
    }

    getRecordedBlob() {
        if (this.recordedBlobs.length === 0) {
            return null;
        }
        return new Blob(this.recordedBlobs, { type: 'audio/webm' });
    }

    showRecordingStatus(message, type = 'info') {
        const statusElement = document.getElementById('recording-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status-message ${type}`;
            
            // Auto-clear after 5 seconds for non-error messages
            if (type !== 'error') {
                setTimeout(() => {
                    statusElement.textContent = '';
                    statusElement.className = 'status-message';
                }, 5000);
            }
        }
    }

    showVoiceConversationStatus(message, type = 'info') {
        const statusElement = document.getElementById('voice-conversation-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `status-message ${type}`;
        }
    }
}

// Audio Upload Handler
async function handleAudioUpload(e) {
    e.preventDefault();
    
    const audioInput = document.getElementById('audio-input');
    const file = audioInput.files[0];
    
    if (!file) {
        alert('Please select an audio file');
        return;
    }

    showLoading('Transcribing audio...');

    try {
        const formData = new FormData();
        formData.append('audio', file);

        const response = await fetch('/audio/transcribe', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            // Display transcription in the question input
            const questionInput = document.getElementById('question-input');
            questionInput.value = result.transcription;
            
            // Show success message
            const statusMsg = document.createElement('div');
            statusMsg.className = 'status-message success';
            statusMsg.innerHTML = `
                <strong>Transcription completed:</strong><br>
                Language: ${result.language}<br>
                Duration: ${result.duration.toFixed(2)}s<br>
                Text: "${result.transcription.substring(0, 100)}..."
            `;
            document.querySelector('.audio-upload').appendChild(statusMsg);
            
            // Auto-remove status message
            setTimeout(() => {
                if (statusMsg.parentNode) {
                    statusMsg.parentNode.removeChild(statusMsg);
                }
            }, 10000);
            
        } else {
            alert(`Transcription failed: ${result.error}`);
        }

    } catch (error) {
        alert(`Transcription failed: ${error.message}`);
    } finally {
        hideLoading();
        audioInput.value = ''; // Clear file input
    }
}

// Voice-to-Voice Conversation Handler
async function handleVoiceConversation() {
    const audioManager = window.audioManager;
    
    if (!audioManager) {
        alert('Audio system not initialized');
        return;
    }

    try {
        audioManager.showVoiceConversationStatus('Starting voice conversation...', 'info');
        
        // Step 1: Record user audio
        await audioManager.startRecording();
        
        // Update button to show it should be clicked to stop
        const voiceBtn = document.getElementById('voice-to-voice');
        const originalText = voiceBtn.innerHTML;
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i> Click to Stop & Process';
        voiceBtn.onclick = async () => {
            // Step 2: Stop recording and process
            audioManager.stopRecording();
            
            // Reset button
            voiceBtn.innerHTML = originalText;
            voiceBtn.onclick = handleVoiceConversation;
            
            // Wait a moment for recording to finalize
            setTimeout(async () => {
                await processVoiceConversation();
            }, 500);
        };

    } catch (error) {
        console.error('Voice conversation failed:', error);
        audioManager.showVoiceConversationStatus('Voice conversation failed', 'error');
    }
}

async function processVoiceConversation() {
    const audioManager = window.audioManager;
    const recordedBlob = audioManager.getRecordedBlob();
    
    if (!recordedBlob) {
        audioManager.showVoiceConversationStatus('No audio recorded', 'error');
        return;
    }

    showLoading('Processing voice conversation...');
    audioManager.showVoiceConversationStatus('Processing your voice input...', 'info');

    try {
        const formData = new FormData();
        formData.append('audio', recordedBlob, 'recorded_audio.webm');
        formData.append('language', 'en');
        formData.append('include_sources', 'true');

        const response = await fetch('/audio/voice-to-voice', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            // Display the conversation
            displayVoiceConversationResult(result);
            audioManager.showVoiceConversationStatus('Voice conversation completed!', 'success');
            
        } else {
            audioManager.showVoiceConversationStatus(`Error: ${result.error}`, 'error');
        }

    } catch (error) {
        console.error('Voice conversation processing failed:', error);
        audioManager.showVoiceConversationStatus('Processing failed', 'error');
    } finally {
        hideLoading();
    }
}

function displayVoiceConversationResult(result) {
    // Update question input with transcribed text
    const questionInput = document.getElementById('question-input');
    questionInput.value = result.user_speech;
    
    // Display AI response
    const responseContent = document.getElementById('response-content');
    responseContent.innerHTML = `
        <div class="voice-conversation-result">
            <div class="user-speech">
                <h4><i class="fas fa-user"></i> You said:</h4>
                <p>"${result.user_speech}"</p>
                <small>Language: ${result.transcription_language}</small>
            </div>
            <div class="ai-response">
                <h4><i class="fas fa-robot"></i> AI Response:</h4>
                <div class="response-text">${result.ai_response_text}</div>
            </div>
            <div class="response-meta">
                <small>
                    <i class="fas fa-clock"></i> 
                    Transcription: ${result.processing_time.transcription.toFixed(2)}s | 
                    Response: ${result.processing_time.llm_response.toFixed(2)}s
                </small>
            </div>
        </div>
    `;
    
    // Play AI response audio
    if (result.ai_response_audio) {
        const audio = document.getElementById('response-audio');
        audio.src = `data:audio/wav;base64,${result.ai_response_audio}`;
        audio.style.display = 'block';
        audio.play();
    }
    
    // Show sources if available
    if (result.sources && result.sources.length > 0) {
        displaySources(result.sources);
    }
    
    // Show response controls
    const responseControls = document.getElementById('response-controls');
    responseControls.style.display = 'flex';
}

// Voice Recording Functions (called from main script)
function startVoiceRecording() {
    if (window.audioManager) {
        window.audioManager.startRecording();
    }
}

function stopVoiceRecording() {
    if (window.audioManager) {
        window.audioManager.stopRecording();
    }
}

function playRecordedAudio() {
    if (window.audioManager) {
        window.audioManager.playRecording();
    }
}

// Initialize audio manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.audioManager = new AudioManager();
    
    // Set up audio-specific event listeners
    const audioUploadForm = document.getElementById('audio-upload-form');
    if (audioUploadForm) {
        audioUploadForm.addEventListener('submit', handleAudioUpload);
    }
});

// Export functions for use in main script
window.AudioFunctions = {
    handleAudioUpload,
    handleVoiceConversation,
    startVoiceRecording,
    stopVoiceRecording,
    playRecordedAudio
};