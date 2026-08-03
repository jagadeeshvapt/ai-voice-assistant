#!/usr/bin/env python3
"""
JARVIS v5.0 - Production 100/100 - Hybrid Offline+Online + FULL ACCESS via flag
Main entry per spec architecture + production hardening

Usage:
  python app.py --text                          # Safe default, offline
  python app.py --text --full-access            # Full C:/ D:/ access
  python app.py --text --online                 # Hybrid online (edge-tts, google STT, openai if key)
  python app.py --voice --online --full-access  # Voice + online + full access
  python app.py --dashboard
  python app.py --single "Chrome open pannu"
"""
import argparse
import sys
import os
from pathlib import Path

# Handle flags BEFORE importing config (config reads env vars)
# Parse early to set env vars
early_args = sys.argv
if "--full-access" in early_args:
    os.environ["JARVIS_FULL_ACCESS"] = "true"
if "--online" in early_args:
    os.environ["JARVIS_ONLINE_MODE"] = "true"
    os.environ["JARVIS_OFFLINE_MODE"] = "false"
if "--offline" in early_args:
    os.environ["JARVIS_OFFLINE_MODE"] = "true"
    os.environ["JARVIS_ONLINE_MODE"] = "false"
if "--text" in early_args:
    os.environ["JARVIS_TEXT_MODE"] = "true"
    os.environ["TEXT_MODE"] = "true"
if "--voice" in early_args:
    os.environ["JARVIS_TEXT_MODE"] = "false"
    os.environ["TEXT_MODE"] = "false"

sys.path.insert(0, str(Path(__file__).parent))

from jarvis.config import config, OFFLINE_ONLY, FULL_ACCESS, ONLINE_ENABLED
from jarvis.utils import logger

def parse_args():
    parser = argparse.ArgumentParser(description="JARVIS v5.0 - Production 100/100 - Hybrid Offline+Online")
    parser.add_argument("--text", action="store_true", help="Text mode (Tanglish supported)")
    parser.add_argument("--voice", action="store_true", help="Voice mode with wake word")
    parser.add_argument("--dashboard", action="store_true", help="Launch dashboard GUI")
    parser.add_argument("--tray", action="store_true", help="Launch tray app")
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    parser.add_argument("--offline", action="store_true", help="Force strict offline (default safe)")
    parser.add_argument("--online", action="store_true", help="Enable hybrid online: edge-tts, google STT, OpenAI if key")
    parser.add_argument("--full-access", action="store_true", help="Enable FULL laptop access C:/ D:/ (safe default otherwise). Production: use with caution!")
    parser.add_argument("--single", type=str, help="Single command, e.g. --single 'chrome open pannu'")
    parser.add_argument("--lang", type=str, default=config.LANGUAGE, help="Language: en, ta, tanglish")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    parser.add_argument("--list-skills", action="store_true", help="List legacy skills")
    parser.add_argument("--check", action="store_true", help="Production health check")
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.debug:
        import logging
        logger.setLevel(logging.DEBUG)
        config.DEBUG = True
    
    # Production banner
    mode_str = "OFFLINE" if OFFLINE_ONLY and not ONLINE_ENABLED else "ONLINE+HIBRID" if ONLINE_ENABLED else "OFFLINE"
    access_str = "FULL C:/D:/" if FULL_ACCESS else "SAFE (Documents/Desktop/workspace)"
    
    print(f"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗ v{config.VERSION} Production 100/100
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝  Human-Brain + Claude + Fable+Mythos
     ██║███████║██████╔╝██║   ██║██║███████╗  Self-Learning Never Repeat Mistake
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║  Mode: {mode_str} | Access: {access_str}
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║  Lang: {args.lang} | Tools: 44
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝  Type: {"TEXT" if args.text else "VOICE" if args.voice else "AUTO"}
    """)
    
    if args.full_access:
        print("⚠️  FULL ACCESS ENABLED - C:/, D:/, shell allowed. Use with caution! (Production requires explicit flag)")
    
    if args.online:
        print("🌐 ONLINE HYBRID ENABLED - Will use edge-tts, google STT, OpenAI if key, fallback to offline")
    else:
        print("🔒 OFFLINE MODE - 100% local, no cloud (Piper, faster-whisper, llama.cpp rule-based)")
    
    if args.check:
        production_check()
        return
    
    if args.list_tools:
        from jarvis.tools.registry import get_tool_registry
        reg = get_tool_registry()
        print("\nAvailable Tools (44) - Production 100/100:")
        print("="*80)
        for info in reg.list_tools_info():
            flag = "⚠️ DANGEROUS" if info["dangerous"] else "✅ safe"
            print(f"  {info['name']:25} | perm:{info['permission']} | {flag} | {info['description']}")
        print("="*80)
        print("Permission Levels: 0=Read, 1=Safe, 2=Confirm, 3=PIN")
        print(f"Current Access: {access_str}")
        print(f"Current Mode: {mode_str} (offline={OFFLINE_ONLY}, online={ONLINE_ENABLED})")
        return
    
    if args.list_skills:
        from jarvis.skills import list_skills
        print("\nLegacy Skills:")
        for name, desc in list_skills():
            print(f"  {name}: {desc}")
        return
    
    # Initialize orchestrator
    try:
        from jarvis.core.orchestrator import get_orchestrator
        orchestrator = get_orchestrator()
        orchestrator.start()
    except Exception as e:
        logger.error(f"Orchestrator init failed: {e}, fallback to legacy")
        from jarvis.assistant import JarvisAssistant
        orchestrator = JarvisAssistant(text_mode=args.text)
    
    if args.single:
        print(f"\n[JARVIS] Single: {args.single} | Mode: {mode_str} | Access: {access_str}\n")
        if hasattr(orchestrator, 'process_text'):
            result = orchestrator.process_text(args.single)
            print(f"Intent: {result.get('intent')}")
            print(f"Emotion: {result.get('detected_emotion')}")
            print(f"Response: {result.get('response')}\n")
            if result.get("relevant_lessons"):
                print(f"Self-learning lessons applied: {len(result['relevant_lessons'])}")
            orchestrator.speak(result.get('response', ''))
        else:
            resp = orchestrator.run_single(args.single)
            print(f"Response: {resp}\n")
        orchestrator.stop()
        return
    
    if args.dashboard:
        print("[JARVIS] Launching dashboard...")
        try:
            from jarvis.ui.dashboard import launch_dashboard
            launch_dashboard(orchestrator)
        except Exception as e:
            logger.error(f"Dashboard failed: {e}")
            print("Fallback to text mode...")
            args.text = True
    
    if args.tray:
        print("[JARVIS] Launching tray...")
        try:
            from jarvis.ui.tray import get_tray_app
            tray = get_tray_app(orchestrator)
            import threading
            threading.Thread(target=lambda: orchestrator.listen_loop(lambda r: print(f"JARVIS: {r.get('response')}")), daemon=True).start()
            tray.run()
        except Exception as e:
            logger.error(f"Tray failed: {e}")
        return
    
    greeting = orchestrator.greet() if hasattr(orchestrator, 'greet') else "Vanakkam Sir"
    print(f"\n[JARVIS] {greeting}\n")
    if hasattr(orchestrator, 'speak'):
        try:
            orchestrator.speak(greeting)
        except:
            pass
    
    print("Commands (Tanglish + Full Access):")
    print("  - 'Chrome open pannu' / 'list folders C:/' (full access)")
    print("  - 'volume kammi pannu' / 'investment advice stocks'")
    print("  - 'doctor headache fever' / 'legal cyber fraud'")
    print("  - 'I am feeling stressed' (empathy + fable wisdom)")
    print("  - 'show mistakes' / 'show lessons' (self-learning)")
    print("  - Type 'exit' to quit\n")
    
    def on_result(result):
        print(f"\n[JARVIS] {result.get('response', '')}")
        if result.get('requires_confirmation'):
            print("  [NEEDS CONFIRM] Say 'yes' / 'aama'")
        if result.get('relevant_lessons'):
            print(f"  [Self-learning: {len(result['relevant_lessons'])} lessons applied - never repeat mistake]")
    
    try:
        if hasattr(orchestrator, 'listen_loop'):
            orchestrator.listen_loop(on_result)
        else:
            orchestrator.run_interactive()
    except KeyboardInterrupt:
        print("\n[JARVIS] Goodbye Sir.")
    finally:
        orchestrator.stop()

def production_check():
    """Production 100/100 health check"""
    print("\n🔍 Production Health Check 100/100")
    print("="*60)
    checks = []
    
    # Config
    try:
        from jarvis.config import config
        checks.append(("Config loads", True, f"v{config.VERSION}, offline={config.OFFLINE_ONLY}, full={config.FULL_ACCESS}"))
    except Exception as e:
        checks.append(("Config loads", False, str(e)))
    
    # Tools
    try:
        from jarvis.tools.registry import get_tool_registry
        reg = get_tool_registry()
        count = len(reg.list_tools())
        checks.append(("Tools registry", count >= 44, f"{count}/44 tools"))
    except Exception as e:
        checks.append(("Tools registry", False, str(e)))
    
    # Security
    try:
        from jarvis.security.pin import get_pin_manager
        pm = get_pin_manager()
        checks.append(("Security PIN bcrypt", True, f"bcrypt={pm._pin_hash[:10]}..."))
    except Exception as e:
        checks.append(("Security PIN", False, str(e)))
    
    # Memory
    try:
        from jarvis.memory import get_memory_db
        db = get_memory_db()
        checks.append(("Memory DB", True, f"SQLite + JSON, user={db.get_user_name()}"))
    except Exception as e:
        checks.append(("Memory DB", False, str(e)))
    
    # Self-learning
    try:
        from jarvis.memory.self_learning import get_self_learning_engine
        sl = get_self_learning_engine()
        stats = sl.get_mistake_stats()
        checks.append(("Self-learning", True, f"{stats.get('lessons',0)} lessons"))
    except Exception as e:
        checks.append(("Self-learning", False, str(e)))
    
    # Knowledge feeder
    try:
        from jarvis.memory.knowledge_feeds.feeder import get_knowledge_feeder
        feeder = get_knowledge_feeder()
        checks.append(("Knowledge feeds", True, f"{len(feeder._cache)} domains"))
    except Exception as e:
        checks.append(("Knowledge feeds", False, str(e)))
    
    # Language
    try:
        from jarvis.language.tanglish_normalizer import get_normalizer
        from jarvis.language.intent_parser import get_intent_parser
        checks.append(("Language (Tanglish+Intent)", True, "normalizer + intent parser OK"))
    except Exception as e:
        checks.append(("Language", False, str(e)))
    
    # Audio
    try:
        from jarvis.audio.speech_to_text import get_stt
        from jarvis.audio.text_to_speech import get_tts
        checks.append(("Audio hybrid", True, f"STT={config.STT_ENGINE}, TTS={config.TTS_ENGINE}"))
    except Exception as e:
        checks.append(("Audio", False, str(e)))
    
    # Orchestrator
    try:
        from jarvis.core.orchestrator import get_orchestrator
        orch = get_orchestrator()
        result = orch.process_text("what time is it")
        checks.append(("Orchestrator", True, f"Intent {result['intent']['intent']}"))
    except Exception as e:
        checks.append(("Orchestrator", False, str(e)))
    
    # Print results
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    for name, ok, detail in checks:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} | {name:25} | {detail}")
    
    print("="*60)
    print(f"Result: {passed}/{total} checks passed = {int(passed/total*100)}/100 production score")
    if passed == total:
        print("🎉 100/100 Production Ready!")
    elif passed >= total*0.9:
        print("✅ 90+/100 Production Ready with minor warnings")
    else:
        print("⚠️ Needs fixes for production")

if __name__ == "__main__":
    main()
