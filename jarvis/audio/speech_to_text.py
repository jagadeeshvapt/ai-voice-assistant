"""
JARVIS Audio - Speech to Text - Production 100/100 - Hybrid Offline+Online - Fixed for Windows without pyaudio
Uses sounddevice directly for mic, so voice works even without pyaudio
"""
import os
import threading
import tempfile
import wave
from typing import Optional, Tuple, Dict

from ..config import config
from ..utils import logger

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    sr = None

class SpeechToText:
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.language = config.LANGUAGE
        self.engine = config.STT_ENGINE
        
        self._faster_model = None
        self._whisper_model = None
        self._sr_recognizer = None
        self._sr_mic = None
        
        self._init_engine()
    
    def _init_engine(self):
        if config.OFFLINE_ONLY and self.engine == "google" and not config.ONLINE_ENABLED:
            self.engine = "faster-whisper"
        
        if self.engine == "auto":
            if config.ONLINE_ENABLED:
                try:
                    import speech_recognition as sr_test
                    self.engine = "google"
                except:
                    self.engine = "faster-whisper"
            else:
                self.engine = "faster-whisper"
        
        if self.engine == "faster-whisper" and FASTER_WHISPER_AVAILABLE:
            try:
                model_path = str(config.STT_MODEL_PATH)
                if not os.path.exists(model_path):
                    logger.info(f"STT model not found at {model_path}, using tiny model")
                    self._faster_model = WhisperModel("tiny", device="cpu", compute_type="int8")
                else:
                    self._faster_model = WhisperModel(model_path, device="cpu", compute_type="int8")
                logger.info("faster-whisper STT loaded")
            except Exception as e:
                logger.error(f"faster-whisper init failed: {e}")
        
        if self.engine in ("whisper", "whisper.cpp") and WHISPER_AVAILABLE:
            try:
                self._whisper_model = whisper.load_model("tiny")
                logger.info("openai-whisper STT loaded (tiny)")
            except Exception as e:
                logger.error(f"whisper init failed: {e}")
        
        if SR_AVAILABLE:
            try:
                self._sr_recognizer = sr.Recognizer()
                self._sr_recognizer.energy_threshold = config.ENERGY_THRESHOLD
                self._sr_recognizer.pause_threshold = config.PAUSE_THRESHOLD
                try:
                    # This requires pyaudio - may fail on Windows without it
                    self._sr_mic = sr.Microphone()
                    with self._sr_mic as source:
                        self._sr_recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    logger.info("SR Microphone with pyaudio available")
                except Exception as e:
                    self._sr_mic = None
                    logger.info(f"SR Microphone pyaudio not available ({e}), will use sounddevice directly for voice - Production fix")
            except Exception as e:
                logger.error(f"SR init failed: {e}")
        
        # Check sounddevice mic as fallback - production fix for Windows without pyaudio
        try:
            from .microphone import get_microphone
            mic = get_microphone()
            if mic.is_available():
                logger.info(f"SoundDevice mic available - voice will work without pyaudio - backend: {mic.backend}")
        except:
            pass
        
        logger.info(f"STT Engine: {self.engine} | faster: {FASTER_WHISPER_AVAILABLE}, whisper: {WHISPER_AVAILABLE}, SR: {SR_AVAILABLE}, mic pyaudio: {self._sr_mic is not None}")

    def transcribe_file(self, wav_path: str) -> Tuple[Optional[str], Dict]:
        meta = {"language": "en", "confidence": 0.8, "engine": self.engine}
        
        if self._faster_model:
            try:
                segments, info = self._faster_model.transcribe(wav_path, language=None, beam_size=5, vad_filter=True)
                text = " ".join([s.text for s in segments]).strip()
                if text:
                    meta["language"] = info.language if hasattr(info, 'language') else "en"
                    meta["confidence"] = 0.95
                    meta["engine"] = "faster-whisper"
                    return text, meta
            except Exception as e:
                logger.error(f"faster-whisper transcribe failed: {e}")
        
        if self._whisper_model:
            try:
                result = self._whisper_model.transcribe(wav_path)
                text = result.get("text", "").strip()
                if text:
                    meta["language"] = result.get("language", "en")
                    meta["engine"] = "whisper"
                    return text, meta
            except Exception as e:
                logger.error(f"whisper transcribe failed: {e}")
        
        if self._sr_recognizer and wav_path:
            try:
                with sr.AudioFile(wav_path) as source:
                    audio = self._sr_recognizer.record(source)
                if config.OFFLINE_ONLY and not config.ONLINE_ENABLED:
                    try:
                        text = self._sr_recognizer.recognize_sphinx(audio)
                        if text:
                            meta["engine"] = "sphinx"
                            return text, meta
                    except:
                        pass
                    return None, meta
                
                # Online mode: try Google first for better accuracy
                if config.ONLINE_ENABLED:
                    try:
                        text = self._sr_recognizer.recognize_google(audio, language="en-IN")
                        if text:
                            meta["engine"] = "google"
                            return text, meta
                    except:
                        pass
                
                try:
                    text = self._sr_recognizer.recognize_sphinx(audio)
                    if text:
                        meta["engine"] = "sphinx"
                        return text, meta
                except:
                    pass
            except Exception as e:
                logger.debug(f"SR transcribe failed: {e}")
        
        return None, meta

    def transcribe_audio_data(self, audio_bytes: bytes) -> Tuple[Optional[str], Dict]:
        if not audio_bytes:
            return None, {}
        tmp = tempfile.mktemp(suffix=".wav")
        try:
            with wave.open(tmp, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_bytes)
            return self.transcribe_file(tmp)
        finally:
            try:
                os.remove(tmp)
            except:
                pass

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 8) -> Optional[str]:
        """PRODUCTION FIX: Works with sounddevice even without pyaudio - Real voice control"""
        # Try sounddevice based recording first (works without pyaudio) - PRODUCTION FIX
        try:
            from .microphone import get_microphone
            from .recorder import get_recorder
            
            mic = get_microphone()
            if mic.is_available():
                logger.info("Listening via sounddevice (no pyaudio needed) - Speak now...")
                print("🎤 Listening via sounddevice - Speak now...")
                recorder = get_recorder()
                audio_bytes = recorder.record_until_silence()
                if audio_bytes and len(audio_bytes) > 1000:
                    text, meta = self.transcribe_audio_data(audio_bytes)
                    if text:
                        from ..utils import user_print
                        user_print(text)
                        logger.info(f"STT via sounddevice success: {text} [{meta}]")
                        return text
                    else:
                        logger.debug("Sounddevice recorded but no transcription")
                        # Fallback to SR google if online
                        if config.ONLINE_ENABLED and self._sr_recognizer:
                            try:
                                # Try to transcribe the same audio via SR google
                                tmp = tempfile.mktemp(suffix=".wav")
                                with wave.open(tmp, 'wb') as wf:
                                    wf.setnchannels(1)
                                    wf.setsampwidth(2)
                                    wf.setframerate(self.sample_rate)
                                    wf.writeframes(audio_bytes)
                                with sr.AudioFile(tmp) as source:
                                    audio = self._sr_recognizer.record(source)
                                try:
                                    text = self._sr_recognizer.recognize_google(audio, language="en-IN")
                                    if text:
                                        from ..utils import user_print
                                        user_print(text)
                                        os.remove(tmp)
                                        return text
                                except:
                                    pass
                                try:
                                    os.remove(tmp)
                                except:
                                    pass
                            except Exception as e:
                                logger.debug(f"Sounddevice + Google fallback failed: {e}")
        except Exception as e:
            logger.debug(f"Sounddevice listen failed: {e}")
        
        # Try SR with pyaudio if available
        if SR_AVAILABLE and self._sr_recognizer and self._sr_mic:
            try:
                with self._sr_mic as source:
                    logger.info("Listening via SR Microphone (pyaudio)...")
                    print("🎤 Listening via pyaudio - Speak now...")
                    audio = self._sr_recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
                wav_data = audio.get_wav_data()
                tmp = tempfile.mktemp(suffix=".wav")
                with open(tmp, 'wb') as f:
                    f.write(wav_data)
                
                text, meta = self.transcribe_file(tmp)
                try:
                    os.remove(tmp)
                except:
                    pass
                
                if text:
                    from ..utils import user_print
                    user_print(text)
                    return text
                
                # Fallback direct SR
                try:
                    return self._sr_recognizer.recognize_sphinx(audio)
                except:
                    if config.ONLINE_ENABLED:
                        try:
                            return self._sr_recognizer.recognize_google(audio, language="en-IN")
                        except:
                            pass
                return None
            except Exception as e:
                logger.debug(f"SR pyaudio listen_once error: {e}")
        
        # Final fallback: text input (when no mic)
        if config.TEXT_MODE:
            return self.listen_text()
        else:
            # In voice mode but no mic works, still allow typing as fallback but inform user
            print("⚠️ No microphone detected or no audio - falling back to text input")
            print("   For voice: Check Windows Settings → Privacy → Microphone → Allow")
            return self.listen_text()

    def listen_text(self) -> Optional[str]:
        try:
            text = input(f"\n[You - Type] > ").strip()
            if text.lower() in ("exit", "quit", "bye", "goodbye jarvis"):
                return text
            return text if text else None
        except (EOFError, KeyboardInterrupt):
            return "exit"

    def has_wake_word(self, text: str) -> bool:
        if not text:
            return False
        low = text.lower()
        for w in config.WAKE_WORDS:
            if w in low:
                return True
        return False

    def extract_command(self, text: str) -> str:
        lower = text.lower()
        for wake in config.WAKE_WORDS:
            if wake in lower:
                lower = lower.replace(wake, "").strip()
        return lower.strip()

_stt_instance = None

def get_stt():
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance
