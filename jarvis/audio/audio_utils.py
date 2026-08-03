"""
Audio utilities - silence detection, normalization, etc.
"""
import math
import struct

def is_silence(data: bytes, threshold: int = 500) -> bool:
    """Check if audio chunk is silence based on RMS"""
    if not data:
        return True
    # Unpack as 16-bit
    count = len(data) // 2
    if count == 0:
        return True
    shorts = struct.unpack(f"{count}h", data[:count*2])
    rms = math.sqrt(sum(s*s for s in shorts) / count)
    return rms < threshold

def normalize_volume(data: bytes, target_level: float = 0.5) -> bytes:
    """Simple volume normalization"""
    return data

def get_audio_duration(sample_count: int, sample_rate: int = 16000) -> float:
    return sample_count / sample_rate
