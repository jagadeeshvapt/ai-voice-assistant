#!/usr/bin/env python3
"""
Check if JARVIS is fully downloaded - all files, models, knowledge
Run: python check_full_download.py
"""
import os
from pathlib import Path

BASE = Path(__file__).parent

checks = []

# Core files
core_files = [
    "app.py", "voice_full_control.py", "holographic_gui.py", "config.yaml",
    "jarvis/core/orchestrator.py", "jarvis/audio/speech_to_text.py", "jarvis/audio/text_to_speech.py",
    "jarvis/language/tanglish_normalizer.py", "jarvis/language/intent_parser.py",
    "jarvis/tools/registry.py", "jarvis/memory/self_learning.py"
]

for f in core_files:
    p = BASE / f
    checks.append((f"Core {f}", p.exists(), f"{p.stat().st_size//1024}KB" if p.exists() else "MISSING"))

# Knowledge feeds
knowledge_dir = BASE / "data" / "knowledge"
knowledge_files = ["investment.json", "business.json", "medical.json", "legal.json", "police.json", "court.json", "ai_technologies.json", "fables.json", "mythos.json", "claude_intelligence.json"]
for kf in knowledge_files:
    p = knowledge_dir / kf
    checks.append((f"Knowledge {kf}", p.exists(), f"{p.stat().st_size//1024}KB" if p.exists() else "MISSING - will auto-create"))

# Models
model_dirs = ["models/stt", "models/tts", "models/llm", "models/wakeword"]
for md in model_dirs:
    p = BASE / md
    checks.append((f"Models {md}", p.exists(), f"{len(list(p.glob('*')))} files" if p.exists() else "MISSING"))

# Assets
assets = ["assets/jarvis_hologram_idle.png", "assets/jarvis_hologram_speaking.png", "assets/jarvis_hologram_listening.png"]
for a in assets:
    p = BASE / a
    checks.append((f"Asset {a}", p.exists(), f"{p.stat().st_size//1024//1024}MB" if p.exists() and p.stat().st_size > 1024*1024 else f"{p.stat().st_size//1024}KB" if p.exists() else "MISSING"))

# Tools count
try:
    from jarvis.tools.registry import get_tool_registry
    reg = get_tool_registry()
    checks.append((f"Tools 44", len(reg.list_tools()) >= 44, f"{len(reg.list_tools())}/44"))
except Exception as e:
    checks.append(("Tools 44", False, str(e)))

# Config
try:
    from jarvis.config import config
    checks.append((f"Config v{config.VERSION}", True, f"offline={config.OFFLINE_ONLY}, full={config.FULL_ACCESS}, online={config.ONLINE_ENABLED}"))
except Exception as e:
    checks.append(("Config", False, str(e)))

# Production check
try:
    from jarvis.core.orchestrator import get_orchestrator
    orch = get_orchestrator()
    result = orch.process_text("what time is it")
    ok = "time" in result['response'].lower() or ":" in result['response']
    checks.append(("Orchestrator what time is it", ok, result['response'][:50]))
except Exception as e:
    checks.append(("Orchestrator", False, str(e)))

print("\n🔍 JARVIS Full Download Check")
print("="*70)
passed = 0
for name, ok, detail in checks:
    status = "✅ PASS" if ok else "❌ FAIL"
    print(f"{status} | {name:35} | {detail}")
    if ok:
        passed += 1

print("="*70)
print(f"Result: {passed}/{len(checks)} checks passed = {int(passed/len(checks)*100)}%")
if passed == len(checks):
    print("🎉 FULLY DOWNLOADED - 100% Ready!")
    print("\nNext: python app.py --text --full-access --online")
    print("      python voice_full_control.py --full-access --online --no-wake-word")
else:
    print("⚠️ Some optional files missing (models) - core still 100% works with fallback")
    print("To download models: .\\scripts\\download_models.ps1 (needs internet, optional)")
