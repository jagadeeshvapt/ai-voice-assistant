"""
JARVIS Audio - Wake Word Detection, strict offline

Priority:
1. openWakeWord (local onnx)
2. simple keyword energy detection + STT match (fallback)

Wakes on: jarvis, hey jarvis, ஜார்விஸ்
"""
import threading
import time
import queue
from typing import Callable, Optional

from ..config import config
from ..utils import logger

try:
    import openwakeword
    from openwakeword.model import Model as OWWModel
    OWW_AVAILABLE = True
except ImportError:
    OWW_AVAILABLE = False
    OWWModel = None

from .microphone import get_microphone
from .speech_to_text import get_stt

class WakeWordDetector:
    def __init__(self):
        self.mic = get_microphone()
        self.stt = get_stt()
        self.engine = config.WAKEWORD_ENGINE
        self._running = False
        self._stop_event = threading.Event()
        self._on_wake: Optional[Callable[[str], None]] = None
        self._oww_model = None
        
        if config.OFFLINE_ONLY and self.engine == "porcupine":
            self.engine = "openwakeword"
        
        # Init openWakeWord if available
        if self.engine == "openwakeword" and OWW_AVAILABLE:
            try:
                # Use default models, or custom jarvis model if exists
                model_path = str(config.WAKEWORD_MODEL_PATH) if config.WAKEWORD_MODEL_PATH.exists() else None
                if model_path:
                    self._oww_model = OWWModel(wakeword_models=[model_path], inference_framework='onnx')
                else:
                    # Default - will use hey_jarvis model if downloaded, else fallback
                    self._oww_model = OWWModel(wakeword_models=["hey_jarvis"], inference_framework='onnx')
                logger.info("openWakeWord model loaded")
            except Exception as e:
                logger.error(f"openWakeWord init failed: {e}, fallback to simple")
                self._oww_model = None
                self.engine = "simple"
        else:
            self.engine = "simple"
        
        logger.info(f"Wake word detector: {self.engine}, words: {config.WAKE_WORDS}")

    def _simple_listen_loop(self):
        """Fallback: use STT to listen for wake word in short phrases"""
        logger.info(f"Wake listening (simple mode) for: {config.WAKE_WORDS}")
        
        while not self._stop_event.is_set():
            try:
                text = self.stt.listen_once(timeout=1, phrase_time_limit=3)
                if not text:
                    continue
                if self.stt.has_wake_word(text):
                    logger.info(f"Wake detected: {text}")
                    command = self.stt.extract_command(text)
                    if not command:
                        # Wake only, listen for follow-up
                        logger.info("Wake only, waiting for command...")
                        follow = self.stt.listen_once(timeout=5, phrase_time_limit=8)
                        command = follow if follow else "hey jarvis"
                    if self._on_wake and command:
                        self._on_wake(command)
            except Exception as e:
                logger.error(f"Wake loop error: {e}")
                time.sleep(0.5)

    def _oww_listen_loop(self):
        """openWakeWord loop - more accurate"""
        import numpy as np
        
        if not self.mic.is_available():
            logger.warning("No mic for OWW, fallback to simple")
            self._simple_listen_loop()
            return
        
        # Start mic
        audio_queue = queue.Queue()
        
        def mic_cb(data: bytes):
            audio_queue.put(data)
        
        self.mic.start(callback=mic_cb)
        
        logger.info("OWW wake listening...")
        buffer = b''
        
        while not self._stop_event.is_set():
            try:
                chunk = audio_queue.get(timeout=0.5)
                buffer += chunk
                
                # Feed to OWW every 1280 samples (80ms at 16k)
                # OWW expects 16-bit mono 16k
                while len(buffer) >= 1280*2:
                    to_process = buffer[:1280*2]
                    buffer = buffer[1280*2:]
                    
                    # Convert bytes to int16 array
                    import struct
                    audio_data = struct.unpack(f"{1280}h", to_process)
                    np_audio = np.array(audio_data, dtype=np.int16)
                    
                    # Predict
                    prediction = self._oww_model.predict(np_audio)
                    # prediction is dict of wakeword -> score
                    for ww, score in prediction.items():
                        if score > 0.5:
                            logger.info(f"OWW detected {ww} score {score}")
                            # After wake, record command
                            from .recorder import get_recorder
                            recorder = get_recorder()
                            audio_bytes = recorder.record_until_silence()
                            if audio_bytes:
                                text, meta = get_stt().transcribe_audio_data(audio_bytes)
                                if text and self._on_wake:
                                    self._on_wake(text)
                            else:
                                if self._on_wake:
                                    self._on_wake("hey jarvis")
                            # Cooldown
                            time.sleep(1.5)
                            buffer = b''
                            break
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"OWW loop error: {e}")
                time.sleep(0.5)

    def start(self, on_wake: Callable[[str], None]):
        self._on_wake = on_wake
        self._stop_event.clear()
        self._running = True
        
        loop_func = self._oww_listen_loop if (self.engine == "openwakeword" and self._oww_model) else self._simple_listen_loop
        
        self._thread = threading.Thread(target=loop_func, daemon=True)
        self._thread.start()
        logger.info("Wake detector started")

    def stop(self):
        self._stop_event.set()
        self._running = False
        try:
            self.mic.stop()
        except:
            pass
        logger.info("Wake detector stopped")

    def is_active(self):
        return self._running

# Singleton
_wake_instance = None

def get_wake_detector() -> WakeWordDetector:
    global _wake_instance
    if _wake_instance is None:
        _wake_instance = WakeWordDetector()
    return _wake_instance

# Backward compat with old wake_word.py
class WakeWordDetectorCompat(WakeWordDetector):
    pass
