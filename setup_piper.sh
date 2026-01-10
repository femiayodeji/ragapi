#!/bin/bash

# Setup script for installing Piper TTS
# This script downloads and installs the Piper TTS binary for local/venv installations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPER_DIR="$SCRIPT_DIR/piper"

echo "Installing Piper TTS..."

# Create piper directory if it doesn't exist
mkdir -p "$PIPER_DIR"

# Check if piper is already installed
if [ -f "$PIPER_DIR/piper/piper" ]; then
    echo "✓ Piper already installed at $PIPER_DIR/piper/piper"
    "$PIPER_DIR/piper/piper" --version
    exit 0
fi

# Download and extract piper
echo "Downloading Piper TTS binary..."
cd "$PIPER_DIR"
wget -q --show-progress https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz

echo "Extracting..."
tar -xzf piper_linux_x86_64.tar.gz
rm piper_linux_x86_64.tar.gz

# Make executable
chmod +x "$PIPER_DIR/piper/piper"

# Test installation
echo ""
echo "✓ Piper TTS installed successfully!"
echo "Version: $("$PIPER_DIR/piper/piper" --version)"
echo "Location: $PIPER_DIR/piper/piper"
