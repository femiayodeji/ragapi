#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPER_DIR="$SCRIPT_DIR/piper"
VOICES_DIR="$SCRIPT_DIR/voices"

echo "Setting up Piper TTS and voice models..."

mkdir -p "$PIPER_DIR"
mkdir -p "$VOICES_DIR"

if [ -f "$PIPER_DIR/piper/piper" ]; then
    echo "✓ Piper already installed"
    "$PIPER_DIR/piper/piper" --version
else
    echo "Downloading Piper TTS binary..."
    cd "$PIPER_DIR"
    wget -q --show-progress https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
    tar -xzf piper_linux_x86_64.tar.gz
    rm piper_linux_x86_64.tar.gz
    chmod +x "$PIPER_DIR/piper/piper"
    echo "✓ Piper TTS installed: $("$PIPER_DIR/piper/piper" --version)"
fi

if [ -f "$VOICES_DIR/en_US-lessac-medium.onnx" ]; then
    echo "✓ Voice model already installed"
else
    echo "Downloading voice model..."
    cd "$VOICES_DIR"
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
    echo "✓ Voice model installed"
fi

echo ""
echo "✓ Setup complete! Voice features ready."
