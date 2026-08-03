# JARVIS Local OS Assistant - Architecture v3.0 (Strict Offline)

This document implements the full A-Z spec from the user's requirement for **Windows PC, Existing PC, Strict Offline, Architecture First**.

## Core Principle: No Cloud API, 100% Local

```
OFFLINE_ONLY=true in config.yaml
No OpenAI, No Google STT, No Azure, No telemetry
All models stored in models/ folder
```

---

## Main Flow

```
Microphone
  ↓
Wake Word Detector (openWakeWord local ONNX)
  ↓
Voice Recording (silence detection 2 sec, max 15 sec)
  ↓
Local Speech-to-Text (faster-whisper local)
  ↓ Tanglish support: "Chrome open pannu", "volume kammi pannu"
Tanglish Normalizer
  ↓ "chrome open pannu" → "open chrome"
  ↓ "volume kammi pannu" → "volume decrease"
  ↓ "enna time?" → "what time"
Intent Router (quick commands without LLM)
  ↓ If confidence < 0.6
Local LLM Planner (llama.cpp Qwen/Mistral GGUF)
  ↓ Returns structured JSON only
  ↓ Example:
  {
    "intent": "open_application",
    "arguments": {"application": "chrome"},
    "language": "ta-en",
    "confidence": 0.96,
    "requires_confirmation": false,
    "permission_level": 1,
    "reply": "Chrome open pannuren."
  }
Permission and Safety Layer
  ↓ Levels:
  ↓ 0 Read-only, 1 Safe, 2 Confirm, 3 PIN
Tool Executor (registry of safe tools)
  ↓
Action Result
  ↓
Local Memory (SQLite jarvis.db + memory.json)
  ↓
Response Formatter (English/Tanglish)
  ↓
Text-to-Speech (Piper TTS local)
  ↓
Speaker
```

---

## Project Structure (Implemented)

```
jarvis/                 # Project root
├── app.py              # New main entry - strict offline, Tanglish
├── main.py             # Legacy entry (v2 compatibility)
├── gui.py              # Tkinter HUD fallback
├── config.yaml         # Main config (offline_only=true)
├── .env.example
├── requirements.txt
│
├── jarvis/             # Package
│   ├── core/
│   │   ├── orchestrator.py   # Main flow controller
│   │   ├── event_bus.py      # Pub/sub events
│   │   ├── state.py          # Assistant state machine
│   │   └── errors.py         # Security errors
│   │
│   ├── audio/
│   │   ├── microphone.py     # sounddevice/pyaudio abstraction
│   │   ├── wake_word.py      # openWakeWord + simple fallback
│   │   ├── recorder.py       # Silence detection recorder
│   │   ├── speech_to_text.py # faster-whisper + whisper + sphinx
│   │   ├── text_to_speech.py # Piper TTS + pyttsx3 fallback
│   │   └── audio_utils.py
│   │
│   ├── language/
│   │   ├── tanglish_normalizer.py  # Tamil/English/Tanglish → normalized
│   │   ├── intent_parser.py        # Quick commands + regex intents
│   │   ├── local_llm.py            # llama.cpp + rule-based fallback
│   │   └── response_formatter.py   # Reply in EN/TA-EN
│   │
│   ├── security/
│   │   ├── permissions.py    # Levels 0-3
│   │   ├── confirmations.py  # Yes/No handling ("aama", "sari")
│   │   ├── pin.py            # PIN verification (default 1234)
│   │   └── audit_log.py      # JSONL audit
│   │
│   ├── memory/
│   │   ├── database.py       # SQLite + JSON backward compat
│   │   ├── preferences.py
│   │   ├── reminders.py      # APScheduler + polling
│   │   └── knowledge_base.py # FTS5 search
│   │
│   ├── tools/                # All abilities as tools
│   │   ├── registry.py       # Tool registry
│   │   ├── applications.py   # open/close apps
│   │   ├── windows.py        # shutdown, restart, lock, sleep
│   │   ├── files.py          # safe file ops with allowlist
│   │   ├── browser.py        # browser automation
│   │   ├── media.py          # volume, media keys, play
│   │   ├── system.py         # status, time, reminders, knowledge
│   │   ├── keyboard_mouse.py # pyautogui
│   │   ├── screenshots.py    # screenshot + OCR
│   │   └── developer.py      # project creation
│   │
│   ├── integrations/         # Future plugins
│   │   ├── android/
│   │   ├── smart_home/
│   │   ├── vlc/
│   │   └── vscode/
│   │
│   ├── ui/
│   │   ├── tray.py           # System tray (pystray)
│   │   ├── dashboard.py      # PySide6 + tkinter fallback
│   │   └── notifications.py  # Desktop notifications
│   │
│   ├── skills/               # Legacy v2 skills (backward compat)
│   └── vision.py             # Optional vision
│
├── models/
│   ├── stt/ (whisper)
│   ├── tts/ (piper voices)
│   ├── llm/ (GGUF)
│   └── wakeword/ (onnx)
│
├── data/
│   ├── jarvis.db (SQLite)
│   ├── memory.json (legacy)
│   ├── audit.log
│   └── logs/
│
├── tests/
│   └── test_*.py
└── scripts/
    ├── install_windows.ps1
    ├── download_models.ps1
    └── start_jarvis.ps1
```

---

## Intent JSON Spec (Strict)

All LLM / planner outputs must be JSON only:

```json
{
  "intent": "open_application",
  "arguments": {"application": "chrome"},
  "language": "ta-en",
  "confidence": 0.96,
  "requires_confirmation": false,
  "permission_level": 1,
  "reply": "Chrome open pannuren."
}
```

Invalid JSON never executes.

---

## Permission Levels

```
LEVEL 0 – Read-only
  get_time, get_date, system_status, search_files, knowledge_query, read_file

LEVEL 1 – Safe action
  open_application, control_volume, take_screenshot, create_file, play_media, lock_screen, set_reminder

LEVEL 2 – Confirmation required
  delete_file, file_operation, send_message, close_application, sleep_system

LEVEL 3 – PIN required (default PIN 1234)
  shutdown_system, restart_system, format, admin_command, door_lock
```

Confirmation flow:
```
User: "shutdown pannu"
JARVIS: "Shutdown panna ellam close aagum. Confirm pannalama? Yes sollunga."
User: "aama" / "yes"
JARVIS: "PIN thappu Sir, sariyana PIN sollunga. Default PIN 1234."
User: "1234"
JARVIS: Executes shutdown
```

Tanglish yes/no:
- Yes: yes, aama, sari, seri, pannu, okay
- No: no, illa, venda, cancel

---

## Tanglish System

### Synonyms handled
```
"open pannu" → "open"
"close pannu" → "close"
"kammi pannu" → "decrease"
"jaasti pannu" → "increase"
"enna time?" → "what time"
"manikku" → "o'clock"
"naalaikku kaalai 7 manikku" → "tomorrow morning at 7"
"adhula" → "in it" (context)
```

### Word order fix
Tamil often says "Chrome open pannu" (Object-Verb) vs English "Open Chrome" (Verb-Object).
Normalizer converts:
```
"chrome open" → "open chrome"
"notepad open pannu" → "open notepad"
```

### Language detection
- English: pure ascii, no Tanglish markers
- Tamil: Unicode \u0B80-\u0BFF
- Tanglish: Contains markers like pannu, da, enna, konjam, manikku

Response adapts:
- User speaks Tanglish → JARVIS replies Tanglish: "Chrome open panniten"
- User speaks English → English: "Opened Chrome"

---

## Security Features

Per spec section S:

- Allowlist / Blocklist folders
```yaml
allowed: ./workspace, Documents, Desktop, C:/Jarvis/workspace
blocked: C:/Windows, Program Files, AppData, /etc, /root
```

- Audit log: JSONL with timestamp, command, intent, result, confirmed

- Confirmation for LEVEL 2, PIN for LEVEL 3

- No silent delete, format, payments, etc.

- `ALLOW_SHELL=false` default

---

## Quick Commands (No LLM, Low Latency)

These bypass LLM for speed:
```
volume up / volume kammi pannu / volume 40
mute / lock screen / take screenshot
open browser / what time is it / enna time
chrome open pannu / pause music
```

Implemented in `intent_parser.py` quick_commands dict with regex.

---

## Local Models (Offline)

| Component | Primary | Fallback | Path |
|-----------|---------|----------|------|
| Wake Word | openWakeWord | simple keyword STT | models/wakeword/ |
| STT | faster-whisper | whisper, sphinx | models/stt/ |
| TTS | Piper TTS | pyttsx3 | models/tts/ |
| LLM | llama.cpp Qwen2-1.5B GGUF | rule-based planner | models/llm/ |
| Vision | Tesseract OCR | - | system |

If models missing, rule-based fallback still works (as tested in sandbox without models).

---

## Testing

```
python tests/test_tanglish.py
python tests/test_intents.py
python tests/test_security.py
python tests/test_orchestrator.py

# Or
pytest tests/
```

---

## Future Phases (Per Spec Section 9)

- Phase 1: Basic local voice ✓ Done
- Phase 2: Wake word ✓ Done (openWakeWord + simple)
- Phase 3: Windows control ✓ Done
- Phase 4: File & browser ✓ Done
- Phase 5: Local LLM brain ✓ Done (llama.cpp + fallback)
- Phase 6: Memory & reminders ✓ Done
- Phase 7: Android - Stub ready
- Phase 8: Smart home - Stub ready
- Phase 9: Vision - Screenshot + OCR done, webcam optional
- Phase 10: Packaging - PS1 scripts + Dockerfile ✓

---

## Why Modular, Not Giant Script

Per spec's last advice: giant script becomes unsafe, slow, unmaintainable.
This architecture is modular, each tool is isolated, permission checked, audited.

## Name

`Jarvis Local OS Assistant` v3.0 - Strict Offline, Tanglish Supported
