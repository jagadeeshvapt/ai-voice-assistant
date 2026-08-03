#!/usr/bin/env python3
"""
JARVIS AI Voice Assistant - Main Entry Point
Just A Rather Very Intelligent System

Usage:
    python main.py                 # Voice mode with wake word
    python main.py --text          # Text chat mode (no mic needed)
    python main.py --single "what time is it"  # Single command
    python main.py --gui           # Launch GUI (calls gui.py)
    python main.py --no-vision     # Disable camera
    python main.py --debug         # Verbose logging
"""

import argparse
import sys
import os
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))

from jarvis.config import config
from jarvis.assistant import JarvisAssistant
from jarvis.utils import logger

def parse_args():
    parser = argparse.ArgumentParser(description="JARVIS AI Voice Assistant")
    parser.add_argument("--text", action="store_true", help="Run in text mode (no microphone needed)")
    parser.add_argument("--voice", action="store_true", help="Force voice mode")
    parser.add_argument("--single", type=str, help="Run a single command and exit, e.g. --single 'what time is it'")
    parser.add_argument("--gui", action="store_true", help="Launch graphical HUD")
    parser.add_argument("--no-vision", action="store_true", help="Disable computer vision")
    parser.add_argument("--enable-vision", action="store_true", help="Enable computer vision")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--list-skills", action="store_true", help="List available skills")
    return parser.parse_args()

def main():
    args = parse_args()

    if args.debug:
        config.DEBUG = True
        logger.setLevel(10)
        logger.info("Debug mode enabled")

    if args.no_vision:
        config.ENABLE_VISION = False
    if args.enable_vision:
        config.ENABLE_VISION = True

    if args.list_skills:
        from jarvis.skills import list_skills
        print("\nAvailable JARVIS Skills:")
        print("=" * 50)
        for name, desc in list_skills():
            print(f"  • {name:20} - {desc}")
        print("=" * 50 + "\n")
        return

    if args.gui:
        # Launch GUI
        try:
            import gui
            gui.main()
        except ImportError as e:
            print(f"GUI dependencies missing: {e}")
            print("Install with: pip install -r requirements.txt and ensure tkinter is available")
            print("Falling back to voice mode...")
            assistant = JarvisAssistant(text_mode=False)
            assistant.run_interactive()
        return

    # Determine mode
    text_mode = config.TEXT_MODE
    if args.text:
        text_mode = True
    if args.voice:
        text_mode = False

    assistant = JarvisAssistant(text_mode=text_mode)

    if args.single:
        print(f"\n[JARVIS] Single command mode: {args.single}\n")
        response = assistant.run_single(args.single)
        print(f"\n[JARVIS] Response: {response}\n")
    else:
        assistant.run_interactive()

if __name__ == "__main__":
    # Print banner
    banner = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
  Just A Rather Very Intelligent System v2.0
    """
    print(banner)
    main()
