"""
Unified audio data format for PyWAC library.

This module provides a standardized way to handle audio data across
all components of the library, ensuring consistency and type safety.
"""

from dataclasses import dataclass
from typing import Union, Optional, Tuple
import numpy as np
import wave
import struct


@dataclass
class AudioData:
    """
    Unified audio data container for PyWAC.
    
    This class represents audio data in a consistent format throughout
    the library, solving the issue of format inconsistencies between
    different layers (C++, Python API, Application).
    
    Attributes:
        samples: Audio samples as numpy array with shape (num_frames, channels)
                 for multi-channel or (num_frames,) for mono
        sample_rate: Sample rate in Hz (e.g., 48000)
        channels: Number of audio channels (1 for mono, 2 for stereo)
    """
    samples: np.ndarray
    sample_rate: int
    channels: int
    
    def __post_init__(self):
        """Validate and normalize the audio data."""
        # Ensure samples is a numpy array
        if not isinstance(self.samples, np.ndarray):
            self.samples = np.array(self.samples)
        
        # Handle different input shapes
        if self.samples.ndim == 1:
            if self.channels == 1:
                # Mono audio - shape is correct
                pass
            elif self.channels == 2:
                # Interleaved stereo data - reshape to (num_frames, 2)
                if len(self.samples) % 2 != 0:
                    # Trim to even number of samples
                    self.samples = self.samples[:-(len(self.samples) % 2)]
                self.samples = self.samples.reshape(-1, 2)
            else:
                raise ValueError(f"Unsupported number of channels: {self.channels}")
        elif self.samples.ndim == 2:
            # Already in (num_frames, channels) format
            if self.samples.shape[1] != self.channels:
                raise ValueError(
                    f"Shape mismatch: samples has {self.samples.shape[1]} channels, "
                    f"but channels={self.channels}"
                )
        else:
            raise ValueError(f"Invalid samples shape: {self.samples.shape}")
    
    @property
    def num_frames(self) -> int:
        """Get the number of audio frames."""
        if self.samples.ndim == 1:
            return len(self.samples)
        return self.samples.shape[0]
    
    @property
    def duration(self) -> float:
        """Get the duration in seconds."""
        return self.num_frames / self.sample_rate
    
    @property
    def dtype(self) -> np.dtype:
        """Get the data type of samples."""
        return self.samples.dtype
    
    def to_float32(self) -> 'AudioData':
        """
        Convert samples to float32 format (-1.0 to 1.0).
        
        Returns:
            New AudioData instance with float32 samples
        """
        if self.dtype == np.float32:
            return self
        
        if self.dtype == np.int16:
            samples_float = self.samples.astype(np.float32) / 32768.0
        elif self.dtype == np.int32:
            samples_float = self.samples.astype(np.float32) / 2147483648.0
        else:
            # Assume it's already some kind of float
            samples_float = self.samples.astype(np.float32)
        
        return AudioData(samples_float, self.sample_rate, self.channels)
    
    def to_int16(self) -> 'AudioData':
        """
        Convert samples to int16 format.
        
        Returns:
            New AudioData instance with int16 samples
        """
        if self.dtype == np.int16:
            return self
        
        if self.dtype == np.float32 or self.dtype == np.float64:
            # Clip to prevent overflow
            samples_clipped = np.clip(self.samples, -1.0, 1.0)
            samples_int16 = (samples_clipped * 32767).astype(np.int16)
        else:
            samples_int16 = self.samples.astype(np.int16)
        
        return AudioData(samples_int16, self.sample_rate, self.channels)
    
    def to_interleaved(self) -> np.ndarray:
        """
        Convert to interleaved format [L0, R0, L1, R1, ...].
        
        Returns:
            1D numpy array with interleaved samples
        """
        if self.channels == 1:
            return self.samples.flatten()
        elif self.samples.ndim == 2:
            return self.samples.flatten()
        else:
            # Already 1D (mono)
            return self.samples
    
    def to_mono(self) -> 'AudioData':
        """
        Convert to mono by averaging channels.
        
        Returns:
            New AudioData instance with mono audio
        """
        if self.channels == 1:
            return self
        
        if self.samples.ndim == 2:
            mono_samples = np.mean(self.samples, axis=1)
        else:
            # Interleaved stereo in 1D
            left = self.samples[0::2]
            right = self.samples[1::2]
            mono_samples = (left + right) / 2
        
        return AudioData(mono_samples, self.sample_rate, 1)
    
    def save(self, filename: str) -> None:
        """
        Save audio data to a WAV file.
        
        Args:
            filename: Output filename
        """
        # Convert to int16 for WAV format
        audio_int16 = self.to_int16()
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            
            # Convert to bytes
            if audio_int16.channels == 1:
                data = audio_int16.samples.tobytes()
            else:
                # Ensure interleaved format for WAV
                data = audio_int16.to_interleaved().tobytes()
            
            wf.writeframes(data)
    
    @classmethod
    def load(cls, filename: str) -> 'AudioData':
        """
        Load audio data from a WAV file.
        
        Args:
            filename: Input filename
            
        Returns:
            AudioData instance
        """
        with wave.open(filename, 'rb') as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            sample_width = wf.getsampwidth()
            num_frames = wf.getnframes()
            
            # Read audio data
            audio_bytes = wf.readframes(num_frames)
            
            # Convert bytes to numpy array based on sample width
            if sample_width == 2:  # 16-bit
                samples = np.frombuffer(audio_bytes, dtype=np.int16)
            elif sample_width == 4:  # 32-bit
                samples = np.frombuffer(audio_bytes, dtype=np.int32)
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # Reshape for multi-channel
            if channels > 1:
                samples = samples.reshape(-1, channels)
            
            return cls(samples, sample_rate, channels)
    
    @classmethod
    def from_interleaved(cls, data: Union[list, np.ndarray], 
                        sample_rate: int = 48000, 
                        channels: int = 2) -> 'AudioData':
        """
        Create AudioData from interleaved audio data.
        
        This is particularly useful for handling data from the C++ layer
        which returns interleaved float32 data.
        
        Args:
            data: Interleaved audio samples [L0, R0, L1, R1, ...]
            sample_rate: Sample rate in Hz
            channels: Number of channels
            
        Returns:
            AudioData instance
        """
        return cls(np.array(data), sample_rate, channels)
    
    def get_statistics(self) -> dict:
        """
        Calculate audio statistics.
        
        Returns:
            Dictionary with RMS, peak, and dB levels
        """
        # Handle empty audio
        if self.num_frames == 0:
            return {
                'rms': 0.0,
                'peak': 0.0,
                'rms_db': -np.inf,
                'peak_db': -np.inf,
                'duration': 0.0,
                'num_frames': 0,
                'sample_rate': self.sample_rate,
                'channels': self.channels
            }
        
        # Convert to float for calculations
        audio_float = self.to_float32()
        
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_float.samples ** 2))
        
        # Calculate peak
        peak = np.max(np.abs(audio_float.samples))
        
        # Calculate dB levels
        rms_db = 20 * np.log10(rms + 1e-10)
        peak_db = 20 * np.log10(peak + 1e-10)
        
        return {
            'rms': float(rms),
            'peak': float(peak),
            'rms_db': float(rms_db),
            'peak_db': float(peak_db),
            'duration': self.duration,
            'num_frames': self.num_frames,
            'sample_rate': self.sample_rate,
            'channels': self.channels
        }
    
    def __repr__(self) -> str:
        """String representation of AudioData."""
        return (
            f"AudioData(duration={self.duration:.2f}s, "
            f"sample_rate={self.sample_rate}Hz, "
            f"channels={self.channels}, "
            f"dtype={self.dtype})"
        )
    
    def __eq__(self, other) -> bool:
        """Check equality with another AudioData instance."""
        if not isinstance(other, AudioData):
            return False
        return (
            np.array_equal(self.samples, other.samples) and
            self.sample_rate == other.sample_rate and
            self.channels == other.channels
        )