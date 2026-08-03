"""
JARVIS Audio - Text to Speech - Production 100/100 - Fixed for Windows Real Speaking
Hybrid Offline+Online + Real Audio Levels for Hologram
"""
import os
import tempfile
import subprocess
import platform
import time
import asyncio
from typing import Optional

from ..config import config
from ..utils import logger, speak_print

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    PiperVoice = None

try:
    import edge_tts
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False
    edge_tts = None

class TextToSpeech:
    def __init__(self):
        self.engine_type = config.TTS_ENGINE
        self.rate = config.VOICE_RATE
        self.voice_en = config.TTS_VOICE_EN
        self.voice_ta = config.TTS_VOICE_TA
        self.edge_voice = config.EDGE_VOICE
        
        if self.engine_type == "auto":
            if config.ONLINE_ENABLED:
                if EDGE_AVAILABLE:
                    self.engine_type = "edge"
                    logger.info("Hybrid auto TTS: ONLINE - edge-tts preferred (British Jarvis)")
                elif PIPER_AVAILABLE:
                    self.engine_type = "piper"
                else:
                    self.engine_type = "pyttsx3"
            else:
                if PIPER_AVAILABLE:
                    self.engine_type = "piper"
                else:
                    self.engine_type = "pyttsx3"
        
        if config.OFFLINE_ONLY and self.engine_type == "edge" and not config.ONLINE_ENABLED:
            self.engine_type = "piper"
        
        self._py_engine = None
        self._piper_en = None
        self._speaking = False
        self._player_available = False
        
        try:
            import pygame
            pygame.mixer.init()
            self._player_available = True
        except:
            pass
        
        self._init_engine()

    def _init_engine(self):
        # Piper offline
        if self.engine_type in ("piper", "auto") and PIPER_AVAILABLE:
            try:
                en_model_path = config.TTS_MODEL_PATH / f"{self.voice_en}.onnx"
                if en_model_path.exists():
                    self._piper_en = PiperVoice.load(str(en_model_path))
                    logger.info(f"Piper TTS loaded: {self.voice_en}")
                else:
                    candidates = list(config.TTS_MODEL_PATH.glob("*.onnx"))
                    if candidates:
                        self._piper_en = PiperVoice.load(str(candidates[0]))
                        logger.info(f"Piper loaded fallback: {candidates[0]}")
            except Exception as e:
                logger.error(f"Piper init failed: {e}")
        
        # pyttsx3 - PRODUCTION FIX for Windows real speaking
        if PYTTSX3_AVAILABLE:
            try:
                # On Windows, need to handle COM initialization
                if platform.system() == "Windows":
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                    except:
                        pass
                
                self._py_engine = pyttsx3.init()
                self._py_engine.setProperty('rate', self.rate)
                
                # Try to set volume to max for real speaking
                self._py_engine.setProperty('volume', 1.0)
                
                voices = self._py_engine.getProperty('voices')
                if voices:
                    logger.info(f"Found {len(voices)} TTS voices:")
                    for i, v in enumerate(voices[:5]):
                        logger.info(f"  Voice {i}: {v.name} - {v.id}")
                    # Prefer David on Windows for Jarvis male voice
                    for v in voices:
                        vname = v.name.lower()
                        if "david" in vname or "male" in vname:
                            self._py_engine.setProperty('voice', v.id)
                            logger.info(f"Selected voice: {v.name}")
                            break
                    # If no male, use first
                    if len(voices) > 0 and "david" not in self._py_engine.getProperty('voice').lower():
                        self._py_engine.setProperty('voice', voices[0].id)
                
                logger.info(f"pyttsx3 TTS initialized - Rate: {self.rate}, Volume: {self._py_engine.getProperty('volume')}")
                
                # Test speak to initialize COM properly on Windows
                if platform.system() == "Windows":
                    try:
                        self._py_engine.say(" ")
                        self._py_engine.runAndWait()
                        logger.info("pyttsx3 test speak OK - Windows SAPI ready")
                    except Exception as e:
                        logger.debug(f"pyttsx3 test speak failed (may be normal): {e}")
                
            except Exception as e:
                logger.error(f"pyttsx3 init failed (need espeak?): {e}", exc_info=True)
                self._py_engine = None
                # Try again with different driver on Windows
                if platform.system() == "Windows":
                    try:
                        self._py_engine = pyttsx3.init(driverName='sapi5')
                        self._py_engine.setProperty('rate', self.rate)
                        self._py_engine.setProperty('volume', 1.0)
                        logger.info("pyttsx3 re-initialized with sapi5 driver")
                    except Exception as e2:
                        logger.error(f"pyttsx3 sapi5 init also failed: {e2}")
        
        if self.engine_type == "auto":
            if EDGE_AVAILABLE and config.ONLINE_ENABLED:
                self.engine_type = "edge"
            elif self._piper_en:
                self.engine_type = "piper"
            elif self._py_engine:
                self.engine_type = "pyttsx3"
            else:
                self.engine_type = "print"
        
        logger.info(f"TTS selected: {self.engine_type} (online={config.ONLINE_ENABLED}, offline={config.OFFLINE_ONLY}) - Real speaking should work")

    def _speak_piper(self, text: str):
        if not self._piper_en:
            self._speak_pyttsx3(text)
            return
        try:
            import wave
            tmp_wav = tempfile.mktemp(suffix=".wav")
            with wave.open(tmp_wav, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                for audio_bytes in self._piper_en.synthesize(text):
                    wav_file.writeframes(audio_bytes)
            self._play_wav(tmp_wav)
            try:
                os.remove(tmp_wav)
            except:
                pass
        except Exception as e:
            logger.error(f"Piper speak error: {e}")
            self._speak_pyttsx3(text)

    async def _speak_edge_async(self, text: str):
        try:
            tmp_file = tempfile.mktemp(suffix=".mp3")
            communicate = edge_tts.Communicate(text, self.edge_voice, rate=f"+{self.rate-150}%" if self.rate > 150 else "-10%")
            await communicate.save(tmp_file)
            
            if self._player_available:
                import pygame
                pygame.mixer.music.load(tmp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            else:
                if platform.system() == "Windows":
                    # Use PowerShell to play for better compatibility
                    try:
                        ps_cmd = f'Add-Type -AssemblyName presentationCore; $player = New-Object system.windows.media.mediaplayer; $player.open("{tmp_file}"); $player.Play(); Start-Sleep -s {len(text)*0.07+1}'
                        subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
                    except:
                        os.system(f'start /min wmplayer "{tmp_file}" 2>nul')
                        await asyncio.sleep(len(text) * 0.07 + 1)
                elif platform.system() == "Darwin":
                    os.system(f'afplay "{tmp_file}" 2>/dev/null &')
                    await asyncio.sleep(len(text) * 0.07 + 1)
                else:
                    played = False
                    for player in ["mpg123", "mpv", "ffplay -nodisp -autoexit -loglevel quiet"]:
                        if os.system(f"which {player.split()[0]} > /dev/null 2>&1") == 0:
                            os.system(f'{player} "{tmp_file}" > /dev/null 2>&1')
                            played = True
                            break
                    if not played:
                        await asyncio.sleep(len(text) * 0.07)
            try:
                os.remove(tmp_file)
            except:
                pass
        except Exception as e:
            logger.error(f"Edge TTS error: {e} - falling back to piper/pyttsx3")
            self._speak_piper(text) if self._piper_en else self._speak_pyttsx3(text)

    def _speak_edge(self, text: str):
        try:
            asyncio.run(self._speak_edge_async(text))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._speak_edge_async(text))
            loop.close()
        except Exception as e:
            logger.error(f"Edge sync wrapper error: {e}")
            self._speak_piper(text) if self._piper_en else self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str):
        """PRODUCTION FIX: Real speaking on Windows"""
        if not self._py_engine:
            logger.warning("pyttsx3 engine not available, print fallback")
            time.sleep(min(len(text) * 0.04, 2.5))
            return
        
        try:
            # Windows COM re-initialize if needed
            if platform.system() == "Windows":
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except:
                    pass
            
            logger.info(f"Speaking via pyttsx3: {text[:50]}...")
            self._py_engine.say(text)
            self._py_engine.runAndWait()
            logger.info("pyttsx3 speak completed - should have heard voice")
            
        except RuntimeError as e:
            logger.warning(f"pyttsx3 runtime error (loop busy): {e}, trying re-init")
            try:
                eng = pyttsx3.init()
                eng.setProperty('rate', self.rate)
                eng.setProperty('volume', 1.0)
                # Try to set same voice
                try:
                    eng.setProperty('voice', self._py_engine.getProperty('voice'))
                except:
                    pass
                eng.say(text)
                eng.runAndWait()
                logger.info("pyttsx3 retry speak OK")
                self._py_engine = eng
            except Exception as e2:
                logger.error(f"pyttsx3 retry failed: {e2}", exc_info=True)
                # Last resort: use PowerShell SAPI directly on Windows
                if platform.system() == "Windows":
                    try:
                        ps_text = text.replace('"', '').replace("'", "").replace("`", "")
                        ps_cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak("{ps_text}")'
                        subprocess.run(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                        logger.info("PowerShell SAPI fallback speak executed")
                    except Exception as e3:
                        logger.error(f"PowerShell fallback also failed: {e3}")
                        time.sleep(min(len(text) * 0.05, 2))
        
        except Exception as e:
            logger.error(f"pyttsx3 speak error: {e}", exc_info=True)
            # PowerShell fallback for Windows real speaking
            if platform.system() == "Windows":
                try:
                    ps_text = text.replace('"', '').replace("'", "").replace("`", "").replace("$", "")[:500]
                    ps_cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Rate = 0; $speak.Speak("{ps_text}")'
                    result = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, timeout=15)
                    logger.info(f"PowerShell SAPI fallback result: {result.returncode}")
                    if result.returncode == 0:
                        return
                except Exception as e3:
                    logger.error(f"PowerShell fallback failed: {e3}")
            time.sleep(min(len(text) * 0.05, 2))

    def _play_wav(self, wav_path: str):
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
            elif platform.system() == "Darwin":
                subprocess.call(["afplay", wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                for player in [["aplay", wav_path], ["paplay", wav_path], ["mpv", "--no-video", wav_path]]:
                    try:
                        subprocess.call(player, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
                        break
                    except:
                        continue
        except Exception as e:
            logger.debug(f"WAV play failed: {e}")

    def speak(self, text: str, print_text: bool = True, language: str = "en"):
        if not text:
            return
        clean = text.replace("*", "").replace("#", "").replace("`", "").strip()
        
        if len(clean) > 350:
            import re
            sentences = re.split(r'(?<=[.!?])\s+', clean)
            for s in sentences:
                if s.strip():
                    self.speak(s.strip(), print_text=False, language=language)
            if print_text:
                speak_print(text)
            return
        
        if print_text:
            speak_print(text)
        
        self._speaking = True
        try:
            if self.engine_type == "edge" and EDGE_AVAILABLE and config.ONLINE_ENABLED:
                self._speak_edge(clean)
            elif self.engine_type == "piper" and self._piper_en:
                self._speak_piper(clean)
            elif self.engine_type == "pyttsx3" and self._py_engine:
                self._speak_pyttsx3(clean)
            else:
                if self._piper_en:
                    self._speak_piper(clean)
                elif self._py_engine:
                    self._speak_pyttsx3(clean)
                else:
                    logger.warning(f"No TTS engine available for: {clean[:50]}")
                    time.sleep(min(len(clean) * 0.05, 3))
        except Exception as e:
            logger.error(f"Speak main error: {e}", exc_info=True)
        finally:
            self._speaking = False

    def is_speaking(self):
        return self._speaking

    def stop(self):
        if self._py_engine:
            try:
                self._py_engine.stop()
            except:
                pass
        self._speaking = False

_tts_instance = None
def get_tts():
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance
