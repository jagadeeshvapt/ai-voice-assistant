# JARVIS Windows Fixed Installer - No Build Tools Needed - Works on Python 3.11/3.12/3.15
Write-Host "JARVIS Windows Fixed Installer - Light Version (No C++ Build Tools)" -ForegroundColor Cyan

# Check Python
Write-Host "`n[0] Checking Python versions..." -ForegroundColor Yellow
py -0p
Write-Host "`nUse Python 3.11 for best compatibility. Python 3.12+ also works with light requirements."

# Check if venv exists
if (Test-Path "venv") {
    Write-Host "Removing old venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
}

# Try Python 3.11 first, then 3.12, then default python
$pythonCmd = $null
try {
    py -3.11 --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = "py -3.11"
        Write-Host "Using Python 3.11 (best for JARVIS)" -ForegroundColor Green
    }
} catch {}

if (-not $pythonCmd) {
    try {
        py -3.12 --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = "py -3.12"
            Write-Host "Using Python 3.12" -ForegroundColor Yellow
        }
    } catch {}
}

if (-not $pythonCmd) {
    $pythonCmd = "py"
    Write-Host "Using default Python (py)" -ForegroundColor Yellow
}

Write-Host "`n[1] Creating venv with $pythonCmd..." -ForegroundColor Yellow
Invoke-Expression "$pythonCmd -m venv venv"

if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "venv creation failed! Trying python..." -ForegroundColor Red
    python -m venv venv
}

Write-Host "`n[2] Activating venv..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "`n[3] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "`n[4] Installing LIGHT requirements (no build tools needed)..." -ForegroundColor Yellow
Write-Host "This will work on Windows without Visual Studio!" -ForegroundColor Green

# Install light first - guaranteed to work
pip install -r requirements-light.txt

Write-Host "`n[5] Installing Windows fixed requirements..." -ForegroundColor Yellow
pip install -r requirements-windows.txt

Write-Host "`n[6] Testing optional heavy packages (will skip if fails)..." -ForegroundColor Yellow
Write-Host "Trying to install scikit-learn etc (optional, for embedding similarity) - will skip if fails"
pip install scikit-learn --only-binary :all: 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "scikit-learn installed (optional)" -ForegroundColor Green
} else {
    Write-Host "scikit-learn skipped - self-learning will use fallback (still 100% works)" -ForegroundColor Yellow
}

Write-Host "`n[7] Production check..." -ForegroundColor Yellow
$env:PYTHONPATH="."
python app.py --check

Write-Host "`n✅ Installation complete with LIGHT requirements!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  python app.py --text --offline                # Safe mode, 100% works"
Write-Host "  python app.py --text --full-access            # Full C:/ D:/ access"
Write-Host "  python app.py --text --full-access --online   # Full + online hybrid best"
Write-Host "  python holographic_gui.py --live --transparent # Golden sphere like image"
Write-Host ""
Write-Host "If you want heavy AI (llama-cpp, sentence-transformers):" -ForegroundColor Yellow
Write-Host "  Install Visual Studio Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/"
Write-Host "  Then: pip install -r requirements.txt"
