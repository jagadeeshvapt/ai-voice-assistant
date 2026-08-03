"""
JARVIS AI Voice Assistant - Local OS Assistant v3.0 Strict Offline
Just A Rather Very Intelligent System
"""
from .config import config

# New architecture
try:
    from .core.orchestrator import get_orchestrator
except:
    get_orchestrator = None

# Backward compat with old v2 architecture
try:
    from .assistant import JarvisAssistant, create_assistant
except:
    JarvisAssistant = None
    create_assistant = None

try:
    from .audio.speech_to_text import get_stt
    from .audio.text_to_speech import get_tts
except:
    from .ears import get_stt
    from .mouth import get_tts

try:
    from .memory import get_memory
except:
    from .memory.database import get_memory

try:
    from .language.local_llm import get_llm as get_brain
except:
    from .brain import get_brain

__version__ = "3.0.0"
__all__ = ["JarvisAssistant", "create_assistant", "config", "get_tts", "get_stt", "get_brain", "get_memory", "get_orchestrator"]
