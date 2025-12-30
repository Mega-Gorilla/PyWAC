"""
Unified recording implementation for PyWAC v0.4.2
Provides a single core recording function that supports all modes.
"""

import os
import sys
import time
import threading
import numpy as np
from typing import Optional, Union, Callable
from .audio_data import AudioData


def _import_process_loopback():
    """Helper function to import pywac.capture module."""
    try:
        from pywac import capture as loopback
        return loopback
    except ImportError:
        return None


def _get_target_pid(target: Optional[Union[str, int]]) -> Optional[int]:
    """
    Get PID from target identifier.
    
    Args:
        target: None (system), process name (str), or PID (int)
        
    Returns:
        PID (0 for system, positive for specific process), or None if not found
    """
    if target is None:
        return 0  # System-wide recording
    
    if isinstance(target, int):
        return target  # Already a PID
    
    if isinstance(target, str):
        # Find process by name
        loopback = _import_process_loopback()
        if loopback is None:
            return None
            
        # First try loopback process list
        processes = loopback.list_audio_processes()
        target_lower = target.lower()
        
        for proc in processes:
            proc_name = getattr(proc, 'name', '')
            if target_lower in proc_name.lower():
                return getattr(proc, 'pid', 0)
        
        # Fallback to PyWAC sessions if not found
        try:
            from . import api
            sessions = api.list_audio_sessions(active_only=True)
            for session in sessions:
                if target_lower in session['process_name'].lower():
                    return session['process_id']
        except:
            pass
        
        return None  # Process not found
    
    return None


def _capture_audio(pid: int, duration: float) -> Optional[AudioData]:
    """
    Core audio capture implementation using pywac.capture.
    
    Args:
        pid: Process ID (0 for system-wide)
        duration: Recording duration in seconds
        
    Returns:
        AudioData object or None if failed
    """
    try:
        loopback = _import_process_loopback()
        if loopback is None:
            return None
        
        # Create capture instance
        capture = loopback.QueueBasedProcessCapture()
        
        # Start capturing
        if not capture.start(pid):
            return None
        
        # Record for specified duration
        start_time = time.time()
        audio_chunks = []
        
        while time.time() - start_time < duration:
            chunks = capture.pop_chunks(max_chunks=100, timeout_ms=10)
            for chunk in chunks:
                if not chunk.get('silent', False):
                    audio_chunks.append(chunk['data'])
            time.sleep(0.01)
        
        # Stop capture
        capture.stop()
        
        # Combine chunks
        if audio_chunks:
            audio_data = np.concatenate(audio_chunks, axis=0)
            return AudioData.from_interleaved(
                data=audio_data.flatten(),
                sample_rate=48000,
                channels=2
            )
        
        # Return empty AudioData with no samples
        return AudioData(np.array([]), 48000, 2)
        
    except Exception:
        return None


def _capture_with_fallback(duration: float) -> AudioData:
    """
    Fallback audio capture using native recorder.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        AudioData object
    """
    from .recorder import AudioRecorder
    recorder = AudioRecorder()
    return recorder.record(duration)


def record(
    duration: float,
    target: Optional[Union[str, int]] = None,
    output_file: Optional[str] = None,
    on_complete: Optional[Callable[[AudioData], None]] = None,
    fallback_enabled: bool = True
) -> Union[AudioData, bool, None]:
    """
    Unified recording function that supports all recording modes.
    
    Args:
        duration: Recording duration in seconds
        target: None for system-wide, process name (str), or PID (int)
        output_file: If specified, save directly to file and return bool
        on_complete: If specified, run asynchronously and call callback with result
        fallback_enabled: If True, fallback to native recorder on failure
        
    Returns:
        - If callback is specified: None (async execution)
        - If filename is specified: bool (success/failure)
        - Otherwise: AudioData object
        
    Examples:
        >>> # System recording (like record_audio)
        >>> audio = record(5)
        
        >>> # Process recording (like record_process)
        >>> success = record(5, target="firefox", output_file="out.wav")
        
        >>> # Callback recording (like record_with_callback)
        >>> record(5, on_complete=lambda audio: audio.save("async.wav"))
        
        >>> # New: Async process recording
        >>> record(5, target="spotify", on_complete=handle_audio)
    """
    # If callback is specified, run asynchronously
    if on_complete is not None:
        def _async_record():
            # Recursive call without callback for sync execution
            audio = record(duration, target, output_file=None, on_complete=None, fallback_enabled=fallback_enabled)
            if audio is not None and isinstance(audio, AudioData):
                on_complete(audio)
        
        thread = threading.Thread(target=_async_record, daemon=True)
        thread.start()
        return None
    
    # Resolve target to PID
    pid = _get_target_pid(target)
    if pid is None:
        # Target not found
        if output_file:
            return False
        return AudioData(np.array([]), 48000, 2)
    
    # Capture audio
    audio_data = _capture_audio(pid, duration)
    
    # Fallback if needed
    if audio_data is None and fallback_enabled and pid == 0:
        # Only fallback for system-wide recording
        audio_data = _capture_with_fallback(duration)
    
    if audio_data is None:
        # Failed to capture
        if output_file:
            return False
        return AudioData(np.array([]), 48000, 2)
    
    # Save to file if requested
    if output_file:
        try:
            audio_data.save(output_file)
            return True
        except Exception:
            return False
    
    # Return AudioData
    return audio_data


class UnifiedRecorder:
    """
    Clean class-based recording interface.
    Provides an intuitive API for all recording modes.
    """
    
    def __init__(self, target: Optional[Union[str, int]] = None):
        """
        Initialize recorder.
        
        Args:
            target: None for system-wide, process name (str), or PID (int)
        """
        self.target = target
        self._target_pid = None
    
    def _ensure_target_resolved(self) -> bool:
        """Ensure target PID is resolved."""
        if self._target_pid is None:
            self._target_pid = _get_target_pid(self.target)
        return self._target_pid is not None
    
    def record(self, duration: float) -> AudioData:
        """
        Synchronous recording.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            AudioData object
        """
        return record(duration, self.target)
    
    def record_to_file(self, duration: float, filename: str) -> bool:
        """
        Record directly to file.
        
        Args:
            duration: Recording duration in seconds
            filename: Output WAV file path
            
        Returns:
            True if successful
        """
        return record(duration, self.target, output_file=filename)
    
    def record_async(self, duration: float, callback: Callable[[AudioData], None]) -> None:
        """
        Asynchronous recording with callback.
        
        Args:
            duration: Recording duration in seconds
            callback: Function called with AudioData when complete
        """
        record(duration, self.target, on_complete=callback)
    
    def is_available(self) -> bool:
        """
        Check if the target process is available for recording.
        
        Returns:
            True if process exists and can be recorded
        """
        return self._ensure_target_resolved()


# Convenience functions for common use cases
def capture_system_audio(duration: float, **kwargs) -> AudioData:
    """Capture system-wide audio."""
    return record(duration, target=None, **kwargs)


def capture_app_audio(app_name: str, duration: float, **kwargs) -> AudioData:
    """Capture audio from a specific application by name."""
    return record(duration, target=app_name, **kwargs)


def capture_process_audio(pid: int, duration: float, **kwargs) -> AudioData:
    """Capture audio from a specific process by PID."""
    return record(duration, target=pid, **kwargs)


# Backward compatibility alias
Recorder = UnifiedRecorder