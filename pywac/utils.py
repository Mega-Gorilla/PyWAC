"""
Utility functions for PyWAC.
"""

import wave
import struct
from typing import List, Tuple, Union
import numpy as np


def convert_float32_to_int16(audio_data: List[float]) -> List[int]:
    """
    Convert float32 audio data to int16.
    
    Args:
        audio_data: List of float32 audio samples (-1.0 to 1.0)
        
    Returns:
        List of int16 audio samples (-32768 to 32767)
    """
    int16_data = []
    for sample in audio_data:
        # Clip to [-1, 1] range
        sample = max(-1.0, min(1.0, sample))
        # Convert to int16
        int16_data.append(int(sample * 32767))
    return int16_data


def save_to_wav(audio_data: Union[List[float], np.ndarray], 
                filename: str, 
                sample_rate: int = 48000, 
                channels: int = 2) -> None:
    """
    Save audio data to a WAV file.
    
    DEPRECATED: Use AudioData.save() instead.
    This function is kept for backward compatibility only.
    
    Args:
        audio_data: Audio samples (float32 or int16)
        filename: Output WAV filename
        sample_rate: Sample rate in Hz
        channels: Number of channels
    """
    import warnings
    warnings.warn(
        "save_to_wav is deprecated. Use AudioData.save() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Convert to list if numpy array
    if hasattr(audio_data, 'tolist'):
        audio_data = audio_data.tolist()
    
    # Handle empty audio data
    if not audio_data or len(audio_data) == 0:
        # Create an empty WAV file
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b'')
        return
    
    # Check if data is float32 or int16
    is_float = isinstance(audio_data[0], float)
    
    if is_float:
        # Convert float32 to int16
        audio_int16 = convert_float32_to_int16(audio_data)
    else:
        # Ensure all values are integers
        audio_int16 = [int(x) for x in audio_data]
    
    # Write WAV file
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Pack audio data as bytes
        if len(audio_int16) > 0:
            packed_data = struct.pack('<%dh' % len(audio_int16), *audio_int16)
            wav_file.writeframes(packed_data)


def load_wav(filename: str) -> Tuple[List[float], int, int]:
    """
    Load audio data from a WAV file.
    
    DEPRECATED: Use AudioData.load() instead.
    This function is kept for backward compatibility only.
    
    Args:
        filename: Input WAV filename
        
    Returns:
        Tuple of (audio_data, sample_rate, channels)
    """
    import warnings
    warnings.warn(
        "load_wav is deprecated. Use AudioData.load() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    with wave.open(filename, 'rb') as wav_file:
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        num_frames = wav_file.getnframes()
        
        # Read audio data
        audio_bytes = wav_file.readframes(num_frames)
        
        # Unpack based on sample width
        if sample_width == 2:  # 16-bit
            audio_int16 = struct.unpack('<%dh' % (len(audio_bytes) // 2), audio_bytes)
            # Convert to float32
            audio_data = [sample / 32768.0 for sample in audio_int16]
        else:
            raise ValueError(f"Unsupported sample width: {sample_width}")
        
        return audio_data, sample_rate, channels


def calculate_rms(audio_data) -> float:
    """
    Calculate RMS (Root Mean Square) of audio data.
    
    Args:
        audio_data: Audio samples (list or numpy array)
        
    Returns:
        RMS value
    """
    import numpy as np
    
    # Convert to numpy array if needed
    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data)
    
    if len(audio_data) == 0:
        return 0.0
    
    # Calculate RMS
    return np.sqrt(np.mean(audio_data ** 2))


def calculate_db(audio_data) -> float:
    """
    Calculate decibel level of audio data.
    
    Args:
        audio_data: Audio samples (list or numpy array)
        
    Returns:
        Decibel level in dB
    """
    import numpy as np
    
    # Convert to numpy array if needed
    if not isinstance(audio_data, np.ndarray):
        audio_data = np.array(audio_data)
    
    if len(audio_data) == 0:
        return -float('inf')
    
    # Calculate RMS
    rms = np.sqrt(np.mean(audio_data ** 2))
    
    if rms == 0:
        return -float('inf')
    
    # Convert to dB (20 * log10(rms))
    import math
    return 20 * math.log10(rms + 1e-10)  # Add small value to avoid log(0)


def normalize_audio(audio_data: List[float], target_level: float = 0.9) -> List[float]:
    """
    Normalize audio data to a target level.
    
    Args:
        audio_data: Audio samples
        target_level: Target peak level (0.0 to 1.0)
        
    Returns:
        Normalized audio data
    """
    if not audio_data:
        return audio_data
    
    # Find peak
    peak = max(abs(sample) for sample in audio_data)
    if peak == 0:
        return audio_data
    
    # Calculate scaling factor
    scale = target_level / peak
    
    # Apply scaling
    return [sample * scale for sample in audio_data]


def get_audio_duration(audio_data: List[float], sample_rate: int = 48000, channels: int = 2) -> float:
    """
    Calculate duration of audio data in seconds.
    
    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        channels: Number of channels
        
    Returns:
        Duration in seconds
    """
    return len(audio_data) / (sample_rate * channels)


def split_channels(audio_data: List[float], channels: int = 2) -> List[List[float]]:
    """
    Split interleaved audio data into separate channels.
    
    Args:
        audio_data: Interleaved audio samples
        channels: Number of channels
        
    Returns:
        List of channel data
    """
    channel_data = [[] for _ in range(channels)]
    
    for i, sample in enumerate(audio_data):
        channel_idx = i % channels
        channel_data[channel_idx].append(sample)
    
    return channel_data


def merge_channels(channel_data: List[List[float]]) -> List[float]:
    """
    Merge separate channels into interleaved audio data.
    
    Args:
        channel_data: List of channel data
        
    Returns:
        Interleaved audio samples
    """
    if not channel_data:
        return []
    
    num_samples = len(channel_data[0])
    interleaved = []
    
    for i in range(num_samples):
        for channel in channel_data:
            if i < len(channel):
                interleaved.append(channel[i])
    
    return interleaved