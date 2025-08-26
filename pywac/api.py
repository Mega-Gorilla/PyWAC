"""
Simple function API for PyWAC.
Provides easy-to-use functions for common audio tasks.
"""

import os
import sys
import numpy as np
from typing import List, Optional, Dict, Any
from .sessions import SessionManager
from .recorder import AudioRecorder
from .audio_data import AudioData


def _import_process_loopback():
    """Helper function to import process_loopback_queue module with path fixes."""
    try:
        import process_loopback_queue as loopback
        return loopback
    except ImportError:
        # Try adding parent directory to path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        try:
            import process_loopback_queue as loopback
            return loopback
        except ImportError:
            return None


# Global instances for convenience functions
_global_session_manager = None
_global_audio_recorder = None


def _get_session_manager() -> SessionManager:
    """Get or create global SessionManager instance."""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = SessionManager()
    return _global_session_manager


def _get_audio_recorder() -> AudioRecorder:
    """Get or create global AudioRecorder instance."""
    global _global_audio_recorder
    if _global_audio_recorder is None:
        _global_audio_recorder = AudioRecorder()
    return _global_audio_recorder


# Session management functions

def list_audio_sessions(active_only: bool = False) -> List[Dict[str, Any]]:
    """
    List all audio sessions.
    
    Args:
        active_only: If True, only return active sessions
        
    Returns:
        List of session information dictionaries
        
    Example:
        >>> sessions = pywac.list_audio_sessions()
        >>> for session in sessions:
        ...     print(f"{session['process_name']}: {session['volume_percent']}%")
    """
    manager = _get_session_manager()
    sessions = manager.list_sessions(active_only=active_only)
    
    return [
        {
            'process_id': s.process_id,
            'process_name': s.process_name,
            'state': s.state_name,
            'is_active': s.is_active,
            'volume': s.volume,
            'volume_percent': int(s.volume * 100),
            'is_muted': s.is_muted
        }
        for s in sessions
    ]


def set_app_volume(app_name: str, volume: float) -> bool:
    """
    Set the volume for an application.
    
    Args:
        app_name: Name or partial name of the application
        volume: Volume level (0.0 to 1.0)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> pywac.set_app_volume("firefox", 0.5)  # Set Firefox to 50%
        True
    """
    manager = _get_session_manager()
    return manager.set_volume(app_name, volume)


def get_app_volume(app_name: str) -> Optional[float]:
    """
    Get the current volume for an application.
    
    Args:
        app_name: Name or partial name of the application
        
    Returns:
        Volume level (0.0 to 1.0), or None if app not found
        
    Example:
        >>> volume = pywac.get_app_volume("firefox")
        >>> print(f"Firefox volume: {volume * 100:.0f}%")
    """
    manager = _get_session_manager()
    return manager.get_volume(app_name)


def mute_app(app_name: str) -> bool:
    """
    Mute an application.
    
    Args:
        app_name: Name or partial name of the application
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> pywac.mute_app("discord")
        True
    """
    manager = _get_session_manager()
    return manager.set_mute(app_name, True)


def unmute_app(app_name: str) -> bool:
    """
    Unmute an application.
    
    Args:
        app_name: Name or partial name of the application
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> pywac.unmute_app("discord")
        True
    """
    manager = _get_session_manager()
    return manager.set_mute(app_name, False)


# Audio recording functions

def _record_with_loopback(pid: int, duration: float) -> Optional[AudioData]:
    """
    Internal function to record audio using process loopback.
    
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
        
        import time
        import numpy as np
        
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
        return None
        
    except Exception:
        return None


def record_audio(duration: float) -> AudioData:
    """
    Record system-wide audio for a specified duration.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        AudioData object containing the recorded audio
        
    Example:
        >>> audio = pywac.record_audio(5)  # Record 5 seconds
        >>> print(f"Recorded {audio.duration:.1f} seconds")
        >>> audio.save("output.wav")
    """
    # Try using process loopback with PID=0 for system-wide recording
    audio_data = _record_with_loopback(0, duration)
    
    if audio_data is not None:
        return audio_data
    
    # Fallback to native recorder if loopback failed
    recorder = _get_audio_recorder()
    return recorder.record(duration)


def record_to_file(filename: str, duration: float) -> bool:
    """
    Record system-wide audio directly to a WAV file.
    
    Args:
        filename: Output WAV filename
        duration: Recording duration in seconds
        
    Returns:
        True if successful
        
    Example:
        >>> pywac.record_to_file("output.wav", 10)  # Record 10 seconds
        True
    """
    try:
        audio = record_audio(duration)
        audio.save(filename)
        return True
    except Exception:
        return False


def record_process(process_name: str, filename: str, duration: float) -> bool:
    """
    Record audio from a specific process only (Windows 10 2004+).
    
    Args:
        process_name: Name or partial name of the process
        filename: Output WAV filename
        duration: Recording duration in seconds
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> pywac.record_process("spotify", "spotify_audio.wav", 10)
        True
        
    Note:
        Requires Windows 10 version 2004 (Build 19041) or later.
        Uses Process Loopback API for process-specific audio capture.
    """
    try:
        loopback = _import_process_loopback()
        if loopback is None:
            return False
        
        # Find process by name
        processes = loopback.list_audio_processes()
        target_pid = None
        
        process_name_lower = process_name.lower()
        for proc in processes:
            proc_name = getattr(proc, 'name', '')
            if process_name_lower in proc_name.lower():
                target_pid = getattr(proc, 'pid', 0)
                break
        
        if target_pid is None:
            return False
        
        return record_process_id(target_pid, filename, duration)
        
    except Exception:
        return False


def record_process_id(pid: int, filename: str, duration: float) -> bool:
    """
    Record audio from a specific process by PID (Windows 10 2004+).
    
    Args:
        pid: Process ID (use 0 for system-wide recording)
        filename: Output WAV filename
        duration: Recording duration in seconds
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> pywac.record_process_id(12345, "app_audio.wav", 10)
        True
        
    Note:
        Requires Windows 10 version 2004 (Build 19041) or later.
        Uses Process Loopback API for process-specific audio capture.
    """
    # Try using process loopback
    audio_data = _record_with_loopback(pid, duration)
    
    if audio_data is None:
        # If PID is 0, try fallback for system recording
        if pid == 0:
            try:
                audio_data = record_audio(duration)
            except Exception:
                return False
        else:
            return False
    
    # Save to WAV file
    try:
        audio_data.save(filename)
        return True
    except Exception:
        return False


def list_recordable_processes() -> List[Dict[str, Any]]:
    """
    List all processes that can be recorded (have audio sessions).
    
    Returns:
        List of process information dictionaries with 'pid' and 'name' keys
        
    Example:
        >>> processes = pywac.list_recordable_processes()
        >>> for proc in processes:
        ...     print(f"{proc['name']} (PID: {proc['pid']})")
        
    Note:
        Requires process_loopback_queue module for process-specific recording.
    """
    try:
        loopback = _import_process_loopback()
        if loopback is None:
            raise ImportError("process_loopback_v2 not available")
        
        processes = loopback.list_audio_processes()
        return [
            {'pid': getattr(proc, 'pid', 0), 'name': getattr(proc, 'name', 'Unknown')}
            for proc in processes
        ]
    except ImportError:
        # Fallback to session-based listing
        sessions = list_audio_sessions(active_only=True)
        seen_pids = set()
        result = []
        
        for session in sessions:
            if session['process_id'] not in seen_pids:
                seen_pids.add(session['process_id'])
                result.append({
                    'pid': session['process_id'],
                    'name': session['process_name']
                })
        
        return result


# Advanced functions

def find_audio_session(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Find an audio session by application name.
    
    Args:
        app_name: Name or partial name of the application
        
    Returns:
        Session information dictionary, or None if not found
        
    Example:
        >>> info = pywac.find_audio_session("firefox")
        >>> if info:
        ...     print(f"Firefox is {'active' if info['is_active'] else 'inactive'}")
    """
    manager = _get_session_manager()
    return manager.get_session_info(app_name)


def find_app(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Deprecated: Use find_audio_session() instead.
    
    Find an application by name and return its audio session info.
    """
    return find_audio_session(app_name)


def get_active_sessions() -> List[str]:
    """
    Get list of process names currently playing audio.
    
    Returns:
        List of process names with active audio sessions
        
    Example:
        >>> active = pywac.get_active_sessions()
        >>> print(f"Active sessions: {', '.join(active)}")
    """
    sessions = list_audio_sessions(active_only=True)
    return [s['process_name'] for s in sessions]


def get_active_apps() -> List[str]:
    """
    Deprecated: Use get_active_sessions() instead.
    
    Get list of applications currently playing audio.
    """
    return get_active_sessions()


def adjust_volume(app_name: str, delta: float) -> Optional[float]:
    """
    Adjust an application's volume by a delta value.
    
    Args:
        app_name: Name or partial name of the application
        delta: Volume change (-1.0 to 1.0)
        
    Returns:
        New volume level, or None if app not found
        
    Example:
        >>> new_volume = pywac.adjust_volume("spotify", 0.1)  # Increase by 10%
        >>> print(f"New volume: {new_volume * 100:.0f}%")
    """
    manager = _get_session_manager()
    current = manager.get_volume(app_name)
    
    if current is None:
        return None
    
    new_volume = max(0.0, min(1.0, current + delta))
    if manager.set_volume(app_name, new_volume):
        return new_volume
    return None


def record_with_callback(duration: float, callback) -> None:
    """
    Record audio asynchronously with a callback.
    
    Args:
        duration: Recording duration in seconds
        callback: Function called when recording completes (receives AudioData)
        
    Example:
        >>> def on_complete(audio):
        ...     print(f"Recording complete: {audio.duration:.1f} seconds")
        ...     audio.save("callback_recording.wav")
        >>> pywac.record_with_callback(5, on_complete)
    """
    from .recorder import AsyncAudioRecorder
    recorder = AsyncAudioRecorder(callback=callback)
    recorder.start_async(duration)