#!/bin/bash

echo "Fixing Whisper installation for audio transcription..."
echo "=================================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "It's recommended to activate your virtual environment first"
    echo ""
fi

# Uninstall the wrong whisper package (graphite whisper)
echo "Step 1: Uninstalling graphite whisper package if present..."
pip uninstall -y whisper 2>/dev/null || echo "Graphite whisper not installed"

# Install the correct OpenAI Whisper package
echo ""
echo "Step 2: Installing OpenAI Whisper package..."
pip install openai-whisper

# Verify installation
echo ""
echo "Step 3: Verifying installation..."
python -c "import whisper; print('✅ OpenAI Whisper installed successfully' if hasattr(whisper, 'load_model') else '❌ Installation failed')"

echo ""
echo "Done! You can now use audio transcription features."