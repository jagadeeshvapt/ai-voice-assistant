"""
Backward compat shim - now uses jarvis.audio.wake_word
"""
from .audio.wake_word import get_wake_detector as _get_wake_impl

class WakeWordDetector:
    def __init__(self):
        self._impl = _get_wake_impl()
    
    def start(self, on_wake):
        return self._impl.start(on_wake)
    
    def stop(self):
        return self._impl.stop()
    
    def is_active(self):
        return self._impl.is_active()

def get_wake_detector():
    return _get_wake_impl()
