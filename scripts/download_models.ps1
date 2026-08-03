# JARVIS - Download Models for Offline Use (Windows PowerShell)
# Run: powershell -ExecutionPolicy Bypass -File scripts/download_models.ps1

Write-Host "JARVIS Model Downloader - Strict Offline" -ForegroundColor Cyan

$modelsDir = Join-Path $PSScriptRoot "..\models"
New-Item -ItemType Directory -Force -Path "$modelsDir\stt" | Out-Null
New-Item -ItemType Directory -Force -Path "$modelsDir\tts" | Out-Null
New-Item -ItemType Directory -Force -Path "$modelsDir\llm" | Out-Null
New-Item -ItemType Directory -Force -Path "$modelsDir\wakeword" | Out-Null

Write-Host "`n[1/4] Downloading faster-whisper tiny model (39MB)..." -ForegroundColor Yellow
# faster-whisper will auto-download on first use, but we can pre-download via python
python -c "from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')"

Write-Host "`n[2/4] Downloading Piper TTS voices..." -ForegroundColor Yellow
# Download English Ryan voice and Tamil voice
$piperUrlEn = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx"
$piperConfigEn = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json"
# Use Invoke-WebRequest if internet available - otherwise manual download needed
try {
    Invoke-WebRequest -Uri $piperUrlEn -OutFile "$modelsDir\tts\en_US-ryan-medium.onnx" -ErrorAction Stop
    Invoke-WebRequest -Uri $piperConfigEn -OutFile "$modelsDir\tts\en_US-ryan-medium.onnx.json" -ErrorAction Stop
    Write-Host "Piper English voice downloaded"
} catch {
    Write-Host "Could not download Piper voices automatically. Please download manually:" -ForegroundColor Red
    Write-Host "  $piperUrlEn -> models/tts/"
}

Write-Host "`n[3/4] Downloading LLM (Qwen 1.5B GGUF, ~1GB)..." -ForegroundColor Yellow
$llmUrl = "https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF/resolve/main/qwen2-1_5b-instruct-q4_k_m.gguf"
try {
    # Use huggingface-cli if available
    huggingface-cli download Qwen/Qwen2-1.5B-Instruct-GGUF qwen2-1_5b-instruct-q4_k_m.gguf --local-dir "$modelsDir\llm" --local-dir-use-symlinks False
} catch {
    Write-Host "Install huggingface-cli: pip install huggingface_hub and run manually"
    Write-Host "  $llmUrl"
}

Write-Host "`n[4/4] Downloading openWakeWord models..." -ForegroundColor Yellow
python -c "import openwakeword; openwakeword.utils.download_models()"

Write-Host "`n✅ Models download attempted. Check models/ folder." -ForegroundColor Green
Write-Host "If offline, copy models manually to models/ folder per README."
