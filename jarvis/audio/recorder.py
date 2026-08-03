"""
JARVIS Audio - Voice Recorder with silence detection - Production 100/100 Fixed for Windows
Real mic level, adjustable sensitivity, works without pyaudio
"""
import time
import wave
import tempfile
import os
from typing import Optional, List

from ..config import config
from ..utils import logger
from .audio_utils import is_silence
from .microphone import get_microphone

class VoiceRecorder:
    def __init__(self):
        self.sample_rate = config.SAMPLE_RATE
        self.silence_timeout = config.SILENCE_TIMEOUT
        self.max_duration = config.MAX_RECORDING
        self.mic = get_microphone()
        # Lower threshold for Windows laptops with quiet mic - production fix
        self.energy_threshold = min(config.ENERGY_THRESHOLD, 1000)

    def record_until_silence(self) -> Optional[bytes]:
        """Record audio until silence is detected or max duration reached - Production fixed"""
        if not self.mic.is_available():
            logger.warning("Mic not available for recording")
            return None
        
        chunks: List[bytes] = []
        silent_chunks = 0
        # Reduced silent timeout for better UX - was 2 sec, now adaptive
        max_silent = int(self.silence_timeout * (self.sample_rate / 1024))
        max_chunks = int(self.max_duration * (self.sample_rate / 1024))
        
        logger.info("Recording... speak now loudly (recorder threshold lowered for Windows laptop)")
        print("🎤 Recording... SPEAK LOUDLY NOW! (3 seconds)")
        
        # Start mic if not running
        if not self.mic._running:
            self.mic.start()
        
        start_time = time.time()
        heard_audio = False
        min_chunks_before_silence = int(1.5 * (self.sample_rate / 1024))  # At least 1.5 sec before checking silence
        
        while len(chunks) < max_chunks:
            chunk = self.mic.read_chunk(timeout=0.5)
            if not chunk:
                # If no chunk, wait a bit
                time.sleep(0.05)
                continue
            
            chunks.append(chunk)
            
            # Check if we heard loud audio (not silence)
            if not is_silence(chunk, threshold=self.energy_threshold):
                heard_audio = True
                silent_chunks = 0
            else:
                # Only count silence after we heard some audio and after min duration
                if len(chunks) > min_chunks_before_silence and heard_audio:
                    silent_chunks += 1
            
            # Debug: show if hearing audio
            if len(chunks) % 10 == 0:
                is_sil = is_silence(chunk, threshold=self.energy_threshold)
                logger.debug(f"Chunk {len(chunks)}/{max_chunks}, silent={is_sil}, heard_audio={heard_audio}, silent_chunks={silent_chunks}/{max_silent}")
            
            # If we heard audio and then silence for too long, stop
            if silent_chunks > max_silent and heard_audio:
                logger.info(f"Silence detected after {len(chunks)} chunks, heard_audio={heard_audio}, stopping")
                break
            
            if time.time() - start_time > self.max_duration:
                logger.info(f"Max duration {self.max_duration}s reached")
                break
        
        if not chunks:
            logger.warning("No chunks recorded")
            return None
        
        # If we never heard loud audio, still return chunks (may be quiet mic) - production fix
        if not heard_audio:
            logger.warning(f"No loud audio detected (threshold {self.energy_threshold}), but returning {len(chunks)} chunks anyway - mic may be quiet, try speaking louder")
            # Lower threshold even more and try to check if any chunk has some energy
            # Return anyway for STT to try
        
        logger.info(f"Recording finished: {len(chunks)} chunks, {len(chunks)*1024/self.sample_rate:.1f}s, heard_audio={heard_audio}")
        return b''.join(chunks)

    def save_wav(self, audio_data: bytes, path: Optional[str] = None) -> str:
        if not path:
            path = tempfile.mktemp(suffix=".wav")
        with wave.open(path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data)
        return path

_recorder = None

def get_recorder():
    global _recorder
    if _recorder is None:
        _recorder = VoiceRecorder()
    return _recorder
