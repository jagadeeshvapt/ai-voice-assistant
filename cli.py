#!/usr/bin/env python3
"""
Simple CLI wrapper for quick testing
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis.assistant import create_assistant

if __name__ == "__main__":
    assistant = create_assistant(text_mode=True)
    print("\nJARVIS CLI - Type commands, 'exit' to quit\n")
    assistant.greet()
    while True:
        try:
            cmd = input("\nYou: ").strip()
            if not cmd:
                continue
            if cmd.lower() in ('exit','quit','bye'):
                print("JARVIS: Goodbye Sir")
                break
            resp = assistant.brain.process(cmd)
            clean = resp.replace("__EXIT__", "")
            print(f"JARVIS: {clean}")
            # Speak if possible
            try:
                assistant.tts.speak(clean)
            except Exception as e:
                pass
            if "__EXIT__" in resp:
                break
        except KeyboardInterrupt:
            break
