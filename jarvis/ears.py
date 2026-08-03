"""
Backward compat shim - now uses jarvis.audio.speech_to_text
"""
from .audio.speech_to_text import get_stt as _get_stt_impl

# Re-export for backward compat
def get_stt_legacy():
    return _get_stt_impl()

# Old class alias
class SpeechToText:
    def __init__(self):
        self._impl = _get_stt_impl()
    
    def listen_once(self, timeout=5, phrase_time_limit=8):
        return self._impl.listen_once(timeout, phrase_time_limit)
    
    def listen_text(self):
        return self._impl.listen_text()
    
    def has_wake_word(self, text):
        return self._impl.has_wake_word(text)
    
    def extract_command(self, text):
        return self._impl.extract_command(text)

# Singleton wrapper - new API
def get_stt():
    return _get_stt_impl()

stt_instance = None
