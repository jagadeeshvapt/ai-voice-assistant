#!/bin/bash
# JARVIS Installation Script - A to Z setup

echo "
 ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗ Installer
 ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
"

set -e

echo "[1/5] Checking Python..."
python3 --version || { echo "Python3 not found!"; exit 1; }

echo "[2/5] Installing system dependencies (Linux)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio espeak espeak-ng ffmpeg scrot || echo "Some optional deps failed, continuing..."
fi

if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install portaudio espeak || echo "brew deps optional"
fi

echo "[3/5] Creating venv..."
python3 -m venv venv || { echo "venv failed, using global"; }
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "[4/5] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[5/5] Setting up config..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ".env created from example - please edit it"
else
    echo ".env already exists"
fi

mkdir -p data
echo "[]" > data/memory.json || true
echo '{"user_name": "Sir", "preferences": {}, "history": [], "todo": [], "reminders": [], "learned_facts": {}}' > data/memory.json

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env: cp .env.example .env && nano .env"
echo "  2. Run text mode: python main.py --text"
echo "  3. Run voice mode: python main.py"
echo "  4. Run GUI: python main.py --gui"
echo "  5. Run API: python server.py"
echo ""
echo "Jarvis ready, Sir."
