"""
Audio recording module for PyWAC with unified AudioData format.
"""

import time
import threading
import numpy as np
from typing import Optional
from datetime import datetime
import pywac._native as _native  # Will be the compiled extension
from .audio_data import AudioData


class AudioRecorder:
    """High-level interface for audio recording."""
    
    def __init__(self, sample_rate: int = 48000, channels: int = 2):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Sample rate in Hz (default: 48000)
            channels: Number of channels (default: 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self._loopback = None
        self._audio_buffer = []
        self._is_recording = False
        self._recording_thread = None
        self._start_time = None
        self._duration = None
    
    def start(self, duration: Optional[float] = None) -> bool:
        """
        Start recording audio.
        
        Args:
            duration: Recording duration in seconds (None for manual stop)
            
        Returns:
            True if recording started successfully
        """
        if self._is_recording:
            raise RuntimeError("Recording is already in progress")
        
        try:
            self._loopback = _native.SimpleLoopback()
            if not self._loopback.start():
                raise RuntimeError("Failed to start loopback capture")
            
            self._audio_buffer = []
            self._is_recording = True
            self._start_time = time.time()
            self._duration = duration
            
            # Start recording thread
            self._recording_thread = threading.Thread(target=self._record_loop)
            self._recording_thread.daemon = True
            self._recording_thread.start()
            
            return True
            
        except Exception as e:
            self._cleanup()
            raise RuntimeError(f"Failed to start recording: {e}")
    
    def stop(self) -> AudioData:
        """
        Stop recording and return the audio data.
        
        Returns:
            AudioData object containing the recorded audio
        """
        # Check if there's anything to stop
        if not self._recording_thread and not self._loopback:
            # Return empty AudioData
            return AudioData(
                samples=np.array([], dtype=np.float32).reshape(0, self.channels),
                sample_rate=self.sample_rate,
                channels=self.channels
            )
        
        # Signal recording to stop
        self._is_recording = False
        
        # Wait for recording thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=1.0)
        
        # Stop loopback if still running
        if self._loopback:
            try:
                self._loopback.stop()
            except:
                pass  # Ignore errors if already stopped
        
        # Get the recorded audio
        audio_data = self._audio_buffer.copy() if self._audio_buffer else []
        
        # Clean up
        self._cleanup()
        
        return audio_data
    
    def _record_loop(self):
        """Internal recording loop (runs in separate thread)."""
        while self._is_recording:
            # Check duration limit
            if self._duration and (time.time() - self._start_time) >= self._duration:
                # Duration reached, stop recording but don't cleanup yet
                self._is_recording = False
                if self._loopback:
                    self._loopback.stop()
                break
            
            # Get audio buffer
            try:
                if self._loopback:
                    buffer = self._loopback.get_buffer()
                    if len(buffer) > 0:
                        self._audio_buffer.extend(buffer)
            except Exception:
                # Ignore errors during recording
                pass
            
            # Small sleep to prevent CPU overuse
            time.sleep(0.01)
    
    def _cleanup(self):
        """Clean up resources."""
        self._loopback = None
        self._audio_buffer = []
        self._is_recording = False
        self._recording_thread = None
        self._start_time = None
        self._duration = None
    
    def _create_audio_data(self, buffer) -> AudioData:
        """
        Create AudioData from raw buffer.
        
        Args:
            buffer: Raw audio buffer from loopback
            
        Returns:
            AudioData object
        """
        if not buffer:
            # Return empty AudioData
            return AudioData(
                samples=np.array([], dtype=np.float32).reshape(0, self.channels),
                sample_rate=self.sample_rate,
                channels=self.channels
            )
        
        # The buffer from SimpleLoopback is interleaved float32 data
        # Convert to AudioData format
        return AudioData.from_interleaved(
            data=buffer,
            sample_rate=self.sample_rate,
            channels=self.channels
        )
    
    def record(self, duration: float) -> AudioData:
        """
        Record audio for a specified duration (blocking).
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            AudioData object containing the recorded audio
        """
        self.start(duration=duration)
        time.sleep(duration)
        return self.stop()
    
    def record_to_file(self, filename: str, duration: float) -> bool:
        """
        Record audio directly to a WAV file.
        
        Args:
            filename: Output WAV filename
            duration: Recording duration in seconds
            
        Returns:
            True if successful
        """
        try:
            audio_data = self.record(duration)
            audio_data.save(filename)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to record to file: {e}")
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording
    
    @property
    def recording_time(self) -> float:
        """Get current recording time in seconds."""
        if self._start_time and self._is_recording:
            return time.time() - self._start_time
        return 0.0
    
    @property
    def sample_count(self) -> int:
        """Get current number of recorded samples."""
        return len(self._audio_buffer)
    
    def get_audio(self) -> AudioData:
        """
        Get current audio buffer without stopping recording.
        
        Returns:
            AudioData object with current buffer content
        """
        return self._create_audio_data(self._audio_buffer.copy())
    
    def save(self, filename: Optional[str] = None) -> str:
        """
        Save current recording to file.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
        
        if not filename.endswith('.wav'):
            filename += '.wav'
        
        audio_data = self.get_audio()
        if audio_data.num_frames == 0:
            raise ValueError("No audio data to save")
        
        audio_data.save(filename)
        return filename


class AsyncAudioRecorder(AudioRecorder):
    """Asynchronous audio recorder with callback support."""
    
    def __init__(self, sample_rate: int = 48000, channels: int = 2, 
                 callback=None):
        """
        Initialize async recorder.
        
        Args:
            sample_rate: Sample rate in Hz
            channels: Number of channels
            callback: Function called when recording completes (receives audio data)
        """
        super().__init__(sample_rate, channels)
        self.callback = callback
    
    def start_async(self, duration: float) -> None:
        """
        Start recording asynchronously.
        
        Args:
            duration: Recording duration in seconds
        """
        def _async_record():
            audio_data = self.record(duration)
            if self.callback:
                # Callback now receives AudioData object
                self.callback(audio_data)
        
        thread = threading.Thread(target=_async_record)
        thread.daemon = True
        thread.start()