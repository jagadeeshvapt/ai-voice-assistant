"""
Backward compat shim - now uses jarvis.audio.text_to_speech
"""
from .audio.text_to_speech import get_tts as _get_tts_impl

class TextToSpeech:
    def __init__(self):
        self._impl = _get_tts_impl()
    
    def speak(self, text, print_text=True):
        return self._impl.speak(text, print_text=print_text)
    
    def is_speaking(self):
        return self._impl.is_speaking()
    
    def stop(self):
        return self._impl.stop()

def get_tts():
    return _get_tts_impl()

tts_instance = None
