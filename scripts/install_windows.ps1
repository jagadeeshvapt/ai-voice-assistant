# JARVIS Windows Installer - Strict Offline Setup
Write-Host "Installing JARVIS Local OS Assistant - Windows" -ForegroundColor Cyan

# Check Python
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found! Install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Create venv
Write-Host "`n[1/4] Creating virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
Write-Host "`n[2/4] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install offline extras
Write-Host "`n[3/4] Installing offline extras (faster-whisper, piper, llama.cpp)..." -ForegroundColor Yellow
pip install faster-whisper piper-tts openwakeword llama-cpp-python psutil pyautogui pywin32 pycaw

# Setup config
Write-Host "`n[4/4] Setting up config and data folders..." -ForegroundColor Yellow
if (-not (Test-Path "config.yaml")) {
    Copy-Item "config.yaml" -Destination "config.yaml" -ErrorAction SilentlyContinue
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" -Destination ".env" -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path "data\logs" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace" | Out-Null

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "Next steps:"
Write-Host "  1. Download models: .\scripts\download_models.ps1 (or manual)"
Write-Host "  2. Edit config.yaml if needed"
Write-Host "  3. Run: python app.py --text"
Write-Host "  4. For voice: python app.py --voice"
