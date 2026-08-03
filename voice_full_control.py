#!/usr/bin/env python3
"""
JARVIS Full Voice Control - Like Real Iron Man JARVIS
Fully voice control, all 44 tools via voice, Tanglish support

Usage:
  python voice_full_control.py                    # Full voice with wake word "Jarvis"
  python voice_full_control.py --no-wake-word    # Continuous listening, no wake word needed (full voice control)
  python voice_full_control.py --full-access     # Full C:/ D:/ access via voice
  python voice_full_control.py --online          # Online hybrid: edge-tts natural voice + google STT
  python voice_full_control.py --tamil           # Tamil/Tanglish voice priority

Voice Commands - All 44 tools work via voice:
  "Jarvis, what time is it" / "Jarvis, enna time"
  "Jarvis, Chrome open pannu"
  "Jarvis, volume kammi pannu" / "Jarvis, volume 50 set pannu"
  "Jarvis, system status sollu"
  "Jarvis, list folders C:/"
  "Jarvis, investment advice for stocks"
  "Jarvis, doctor headache fever"
  "Jarvis, take screenshot"
  "Jarvis, lock screen pannu"
  "Jarvis, shutdown pannu" -> will ask "Confirm pannalama? Yes sollunga" -> say "aama"
"""
import argparse
import sys
import os
from pathlib import Path

# Handle flags before config import
early = sys.argv
if "--full-access" in early:
    os.environ["JARVIS_FULL_ACCESS"] = "true"
if "--online" in early:
    os.environ["JARVIS_ONLINE_MODE"] = "true"
    os.environ["JARVIS_OFFLINE_MODE"] = "false"
if "--tamil" in early:
    os.environ["LANGUAGE"] = "tanglish"

sys.path.insert(0, str(Path(__file__).parent))

from jarvis.config import config
from jarvis.utils import logger

def main():
    parser = argparse.ArgumentParser(description="JARVIS Full Voice Control - Real Iron Man")
    parser.add_argument("--no-wake-word", action="store_true", help="No wake word needed - continuous listening, fully voice control")
    parser.add_argument("--full-access", action="store_true", help="Full C:/ D:/ access")
    parser.add_argument("--online", action="store_true", help="Online hybrid: natural voice Edge-TTS + Google STT")
    parser.add_argument("--offline", action="store_true", help="Strict offline")
    parser.add_argument("--tamil", action="store_true", help="Tamil/Tanglish priority")
    parser.add_argument("--wake-word", type=str, default="jarvis", help="Custom wake word (default jarvis)")
    parser.add_argument("--list-voice-commands", action="store_true", help="List all voice commands")
    args = parser.parse_args()

    if args.list_voice_commands:
        print("""
🎤 JARVIS Full Voice Control - All Voice Commands (44 tools)

Basic:
  "Jarvis, what time is it" / "enna time" / "time sollu"
  "Jarvis, system status sollu"
  "Jarvis, enna date"

Volume & Media (Tanglish):
  "Jarvis, volume kammi pannu" / "volume up / down / 50 / mute"
  "Jarvis, play music" / "pause music" / "next song"

Apps - Full Laptop:
  "Jarvis, Chrome open pannu" / "Notepad open pannu" / "VS Code open pannu"
  "Jarvis, close chrome pannu"
  "Jarvis, list folders C:/" / "search files resume in C:/"

Files - Full Access:
  "Jarvis, create file C:/test.txt"
  "Jarvis, read file C:/test.txt"
  "Jarvis, take screenshot"

Knowledge Domains - Human Brain:
  "Jarvis, investment advice for stocks"
  "Jarvis, business startup idea"
  "Jarvis, doctor headache fever"
  "Jarvis, legal advice for cyber fraud"
  "Jarvis, police FIR process sollu"
  "Jarvis, how to build JARVIS AI"
  "Jarvis, I am feeling stressed today" (empathy + fable wisdom)

Self-Learning:
  "Jarvis, show mistakes"
  "Jarvis, show lessons"
  If JARVIS wrong: "No, correct is open chrome browser" -> learns never repeat

Autonomous:
  "Jarvis, build a portfolio website project"

Security:
  "Jarvis, shutdown pannu" -> JARVIS: "Confirm pannalama?" -> You: "aama" or "yes" -> PIN "1234"

In No-Wake-Word Mode (--no-wake-word):
  Just speak directly without saying Jarvis: "what time is it", "Chrome open pannu"
        """)
        return

    # Banner
    mode = "ONLINE+OFFLINE Hybrid" if args.online else "OFFLINE 100% Local"
    access = "FULL C:/D:/" if args.full_access else "SAFE"
    wake = "No Wake Word - Continuous" if args.no_wake_word else f"Wake Word: '{args.wake_word}'"
    
    print(f"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗ v{config.VERSION} FULL VOICE CONTROL
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝  Real Iron Man JARVIS
     ██║███████║██████╔╝██║   ██║██║███████╗  44 Tools via Voice + Tanglish
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║  Mode: {mode} | Access: {access}
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║  {wake}
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝  Voice: {'Tanglish Priority' if args.tamil else 'English+Tanglish Auto'}

🎤 FULL VOICE CONTROL READY

How to speak:
  {"Just speak directly - no need to say Jarvis" if args.no_wake_word else "1. Say wake word: 'Jarvis' or 'Hey Jarvis' clearly"}
  {"2. Wait for JARVIS to say 'Yes Sir?'" if not args.no_wake_word else "2. JARVIS listens continuously"}
  3. Speak command: "what time is it", "Chrome open pannu", "volume kammi pannu"
  4. JARVIS will speak response

Tips for good voice recognition:
  - USB mic or good laptop mic, quiet room
  - Speak clearly, not too fast
  - Tanglish works: "Chrome open pannu", "volume kammi pannu"
  - Say "exit" or "bye jarvis" to quit

Starting...
    """)

    # Initialize orchestrator
    try:
        from jarvis.core.orchestrator import get_orchestrator
        from jarvis.core.state import get_state_manager
        orch = get_orchestrator()
        state_mgr = get_state_manager()
        orch.start()
        
        greeting = orch.greet()
        print(f"\n[JARVIS Voice] {greeting}\n")
        orch.speak(greeting)
        
    except Exception as e:
        print(f"Failed to init JARVIS: {e}")
        import traceback
        traceback.print_exc()
        return

    # Voice loop
    if args.no_wake_word:
        # Continuous listening - fully voice control, no wake word needed
        print("\n🎤 CONTINUOUS LISTENING MODE - No wake word needed, just speak!")
        print("Say 'what time is it' or 'Chrome open pannu' directly")
        print("Say 'exit' or 'bye' to quit\n")
        
        from jarvis.audio.speech_to_text import get_stt
        
        stt = get_stt()
        
        try:
            while True:
                try:
                    print("\n🎤 Listening... speak now (or type if no mic)")
                    text = stt.listen_once(timeout=10, phrase_time_limit=8)
                    
                    if not text:
                        # Try text fallback
                        text = stt.listen_text()
                    
                    if not text:
                        continue
                    
                    low = text.lower().strip()
                    if low in ("exit", "quit", "bye", "bye jarvis", "goodbye", "stop"):
                        print("Goodbye Sir!")
                        orch.speak("Goodbye Sir, going offline")
                        break
                    
                    # Remove wake word if present even in no-wake mode
                    if stt.has_wake_word(text):
                        text = stt.extract_command(text)
                        if not text:
                            continue
                    
                    print(f"You said: {text}")
                    
                    # Production fix: ignore single short words that are not valid commands
                    low_text = text.lower().strip()
                    if low_text in ("jarvis", "hey jarvis", "ok jarvis", "primary") or len(low_text.split()) == 1 and len(low_text) < 6:
                        # If just wake word or single short nonsense word, ask for real command
                        if low_text == "jarvis" or low_text == "hey jarvis":
                            print("[JARVIS] You said just 'Jarvis' - now say command like 'what time is it' or 'Chrome open pannu'")
                            orch.speak("Yes Sir, how can I help?")
                            continue
                        # Check if single word is valid command
                        if low_text in ("primary", "hello", "hi"):
                            print(f"[JARVIS] '{text}' is not a valid command - try 'what time is it' or 'Chrome open pannu'")
                            print("Valid voice commands: what time is it, enna time, system status sollu, Chrome open pannu, volume kammi pannu, investment advice, show mistakes")
                            # Don't process as knowledge query
                            continue
                    
                    # Process
                    result = orch.process_text(text)
                    response = result.get('response', '')
                    print(f"\n[JARVIS Voice] {response}\n")
                    
                    # Speak response - full voice control
                    orch.speak(response)
                    
                    # Show if self-learning applied
                    if result.get('relevant_lessons'):
                        print(f"[Self-learning: {len(result['relevant_lessons'])} lessons applied - never repeat mistake]")
                    
                    if result.get('requires_confirmation'):
                        print("[Needs confirmation - say 'yes' or 'aama']")
                
                except KeyboardInterrupt:
                    print("\nInterrupted - Goodbye Sir!")
                    break
                except Exception as e:
                    logger.error(f"Voice loop error: {e}")
                    print(f"Error: {e}, continuing...")
                    continue
        
        finally:
            orch.stop()
    
    else:
        # Wake word mode - like real JARVIS
        print(f"\n🎤 WAKE WORD MODE - Say '{args.wake_word}' then command")
        print(f"Example: '{args.wake_word}, what time is it' or '{args.wake_word}, Chrome open pannu'")
        print("Say 'exit' to quit\n")
        
        from jarvis.audio.wake_word import get_wake_detector
        
        wake_detector = get_wake_detector()
        
        def on_wake_command(command: str):
            try:
                print(f"\n🔔 Wake word detected! Command: {command}")
                
                if not command or command.strip().lower() in ("hey jarvis", "jarvis", args.wake_word):
                    # Just wake word, ask for command
                    wake_response = "Yes Sir, how can I help?"
                    print(f"[JARVIS] {wake_response}")
                    orch.speak(wake_response)
                    
                    # Listen for follow-up
                    from jarvis.audio.speech_to_text import get_stt
                    stt = get_stt()
                    follow = stt.listen_once(timeout=8, phrase_time_limit=8)
                    if follow:
                        command = follow
                    else:
                        return
                
                print(f"Processing: {command}")
                result = orch.process_text(command)
                response = result.get('response', '')
                print(f"[JARVIS Voice] {response}\n")
                orch.speak(response)
                
                if result.get('requires_confirmation'):
                    print("Say 'yes' or 'aama' to confirm, or 'no'/'illa' to cancel")
            
            except Exception as e:
                logger.error(f"Wake command error: {e}")
                print(f"Error: {e}")
        
        try:
            wake_detector.start(on_wake_command)
            print(f"Listening for wake word '{args.wake_word}'... (say it clearly)")
            print("Press Ctrl+C to exit")
            
            # Keep alive
            import time
            while True:
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\nGoodbye Sir!")
        finally:
            wake_detector.stop()
            orch.stop()

if __name__ == "__main__":
    main()
