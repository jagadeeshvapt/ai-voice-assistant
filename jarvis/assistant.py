"""
JARVIS Assistant - Main orchestrator
Combines Ears, Brain, Mouth, Vision, Memory, Skills into one JARVIS experience
"""
import threading
import time
import datetime
import signal
import sys
from typing import Optional

from .config import config
from .utils import logger, get_greeting, speak_print
from .ears import get_stt
from .mouth import get_tts
from .brain import get_brain
from .memory import get_memory
from .vision import get_vision
from .wake_word import WakeWordDetector

class JarvisAssistant:
    def __init__(self, text_mode: bool = None):
        # Override text_mode if provided
        if text_mode is not None:
            config.TEXT_MODE = text_mode
        
        self.config = config
        self.memory = get_memory()
        self.stt = get_stt()
        self.tts = get_tts()
        self.brain = get_brain()
        self.vision = get_vision()
        self.wake_detector = WakeWordDetector()
        
        self._running = False
        self._stop_event = threading.Event()
        self._reminder_thread = None
        
        logger.info(f"JARVIS Initialized - Text Mode: {config.TEXT_MODE}, Vision: {config.ENABLE_VISION}")

    def _reminder_loop(self):
        """Background thread to check reminders"""
        while not self._stop_event.is_set():
            try:
                due = self.memory.get_due_reminders()
                for r in due:
                    msg = f"Reminder, sir: {r['text']}"
                    self.tts.speak(msg)
                    self.memory.mark_reminder_triggered(r)
                time.sleep(10)
            except Exception as e:
                logger.error(f"Reminder loop error: {e}")
                time.sleep(10)

    def greet(self):
        greeting = get_greeting()
        user_name = self.memory.data.get('user_name', 'Sir')
        now = datetime.datetime.now().strftime("%I:%M %p on %A, %B %d")
        
        msg = f"{greeting}, {user_name}. It's {now}. "
        
        # Add system status
        if config.ENABLE_VISION and self.vision.enabled:
            v_status = self.vision.get_status()
            msg += f"{v_status}. "
        
        # Pending todos/reminders
        todos = self.memory.list_todo()
        if todos:
            msg += f"You have {len(todos)} pending tasks. "
        
        pending_rem = [r for r in self.memory.data.get("reminders", []) if not r.get("triggered")]
        if pending_rem:
            msg += f"And {len(pending_rem)} reminders set. "
        
        msg += "How can I assist you today?"
        
        self.tts.speak(msg)
        return msg

    def process_input(self, text: str) -> str:
        """Process single input and return response, handling exit"""
        response = self.brain.process(text)
        
        # Check for exit marker
        should_exit = "__EXIT__" in response
        clean_response = response.replace("__EXIT__", "").strip()
        
        # Speak response
        self.tts.speak(clean_response)
        
        if should_exit:
            self.shutdown()
        
        return clean_response

    def _on_wake_command(self, command: str):
        """Called when wake word detected + command extracted"""
        logger.info(f"Wake command: {command}")
        if not command or command.strip().lower() in ("hey jarvis", "jarvis"):
            # Just wake word, ask for command
            self.tts.speak("Yes sir, how can I help?")
            # Listen for follow-up
            follow = self.stt.listen_once(timeout=5, phrase_time_limit=8)
            if follow:
                self.process_input(follow)
        else:
            self.process_input(command)

    def run_interactive(self):
        """Run in interactive loop - text or voice"""
        self._running = True
        self._stop_event.clear()
        
        # Start reminder thread
        self._reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
        self._reminder_thread.start()
        
        # Start vision if enabled
        if config.ENABLE_VISION:
            self.vision.start()
        
        # Greeting
        try:
            self.greet()
        except Exception as e:
            logger.error(f"Greeting failed: {e}")

        # Signal handlers for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Interrupt received, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        print("\n" + "="*60)
        print(f"  JARVIS AI VOICE ASSISTANT - Ready")
        print(f"  Mode: {'TEXT' if config.TEXT_MODE else 'VOICE'} | Say '{config.WAKE_WORDS[0]}' to activate")
        print(f"  Type 'exit' or 'quit' to stop")
        print(f"  Commands: time, weather, open [app], search [query], play [song], joke, todo, reminders, etc.")
        print("="*60 + "\n")

        if config.TEXT_MODE:
            # Simple text loop
            while self._running and not self._stop_event.is_set():
                try:
                    text = self.stt.listen_text()
                    if not text:
                        continue
                    low = text.lower().strip()
                    if low in ("exit", "quit", "bye", "goodbye", "shutdown"):
                        self.tts.speak(f"Goodbye {self.memory.data.get('user_name','Sir')}, shutting down")
                        break
                    
                    # Remove wake word if present
                    if self.stt.has_wake_word(text):
                        text = self.stt.extract_command(text)
                        if not text:
                            continue
                    
                    self.process_input(text)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Text loop error: {e}")
                    time.sleep(0.5)
        else:
            # Voice mode with wake word
            try:
                # First try continuous wake word detection
                print(f"[JARVIS] Listening for wake word: {config.WAKE_WORDS} ...")
                print("[JARVIS] Or just start talking - I'm always listening in this mode")
                
                self.wake_detector.start(self._on_wake_command)
                
                # Keep main thread alive
                while self._running and not self._stop_event.is_set():
                    time.sleep(0.5)
                    
                    # Also check if wake detector died
                    if not self.wake_detector.is_active() and self._running:
                        logger.warning("Wake detector inactive, restarting...")
                        self.wake_detector.start(self._on_wake_command)
            
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt - shutting down")
            finally:
                self.shutdown()

    def run_single(self, command: str):
        """Run single command and exit - useful for testing or API"""
        self._running = True
        # Start vision briefly if needed
        if config.ENABLE_VISION:
            self.vision.start()
        
        response = self.brain.process(command)
        clean = response.replace("__EXIT__", "").strip()
        self.tts.speak(clean)
        return clean

    def shutdown(self):
        logger.info("Shutting down JARVIS...")
        self._running = False
        self._stop_event.set()
        try:
            self.wake_detector.stop()
        except:
            pass
        try:
            self.vision.stop()
        except:
            pass
        try:
            self.tts.stop()
        except:
            pass
        print("\n[JARVIS] Offline.\n")

# Convenience function
def create_assistant(text_mode: bool = False) -> JarvisAssistant:
    return JarvisAssistant(text_mode=text_mode)
