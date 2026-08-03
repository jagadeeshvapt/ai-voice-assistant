"""
JARVIS Audio - Microphone abstraction, strict offline
Supports sounddevice, pyaudio, or dummy for testing
"""
import threading
import time
import queue
from typing import Optional, Callable

from ..config import config
from ..utils import logger

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

class Microphone:
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.chunk_size = 1024
        self._running = False
        self._stream = None
        self._audio_queue = queue.Queue()
        
        if SOUNDDEVICE_AVAILABLE:
            logger.info("Microphone using sounddevice")
            self.backend = "sounddevice"
        elif PYAUDIO_AVAILABLE:
            logger.info("Microphone using pyaudio")
            self.backend = "pyaudio"
        else:
            logger.warning("No microphone backend available - text mode only")
            self.backend = "dummy"

    def start(self, callback: Callable[[bytes], None] = None):
        if self.backend == "dummy":
            return False
        
        self._running = True
        try:
            if self.backend == "sounddevice":
                def audio_callback(indata, frames, time_info, status):
                    if status:
                        logger.debug(f"Audio status: {status}")
                    self._audio_queue.put(bytes(indata))
                    if callback:
                        callback(bytes(indata))
                
                self._stream = sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=self.chunk_size,
                    dtype='int16',
                    channels=1,
                    callback=audio_callback
                )
                self._stream.start()
            else:
                # pyaudio
                self._p = pyaudio.PyAudio()
                self._stream = self._p.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    frames_per_buffer=self.chunk_size,
                    stream_callback=lambda in_data, frame_count, time_info, status: (callback(in_data) if callback else None, pyaudio.paContinue)
                )
                self._stream.start_stream()
            logger.info("Microphone started")
            return True
        except Exception as e:
            logger.error(f"Microphone start failed: {e}")
            self._running = False
            return False

    def stop(self):
        self._running = False
        try:
            if self._stream:
                self._stream.stop()
                if hasattr(self._stream, 'close'):
                    self._stream.close()
        except Exception as e:
            logger.error(f"Mic stop error: {e}")

    def read_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def is_available(self) -> bool:
        return self.backend != "dummy"

    def list_devices(self):
        if SOUNDDEVICE_AVAILABLE:
            try:
                return sd.query_devices()
            except:
                return []
        return []

# Singleton
_mic_instance = None

def get_microphone() -> Microphone:
    global _mic_instance
    if _mic_instance is None:
        _mic_instance = Microphone()
    return _mic_instance
