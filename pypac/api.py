"""
Simple function API for PyPAC.
Provides easy-to-use functions for common audio tasks.
"""

from typing import List, Optional, Dict, Any
from .sessions import SessionManager
from .recorder import AudioRecorder


# Global instances for convenience functions
_session_manager = None
_audio_recorder = None


def _get_session_manager() -> SessionManager:
    """Get or create global SessionManager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def _get_audio_recorder() -> AudioRecorder:
    """Get or create global AudioRecorder instance."""
    global _audio_recorder
    if _audio_recorder is None:
        _audio_recorder = AudioRecorder()
    return _audio_recorder


# Session management functions

def list_audio_sessions(active_only: bool = False) -> List[Dict[str, Any]]:
    """
    List all audio sessions.
    
    Args:
        active_only: If True, only return active sessions
        
    Returns:
        List of session information dictionaries
        
    Example:
        >>> sessions = pypac.list_audio_sessions()
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
        >>> pypac.set_app_volume("firefox", 0.5)  # Set Firefox to 50%
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
        >>> volume = pypac.get_app_volume("firefox")
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
        >>> pypac.mute_app("discord")
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
        >>> pypac.unmute_app("discord")
        True
    """
    manager = _get_session_manager()
    return manager.set_mute(app_name, False)


# Audio recording functions

def record_audio(duration: float) -> List[float]:
    """
    Record audio for a specified duration.
    
    Args:
        duration: Recording duration in seconds
        
    Returns:
        List of audio samples (float32)
        
    Example:
        >>> audio_data = pypac.record_audio(5)  # Record 5 seconds
        >>> print(f"Recorded {len(audio_data)} samples")
    """
    recorder = _get_audio_recorder()
    return recorder.record(duration)


def record_to_file(filename: str, duration: float) -> bool:
    """
    Record audio directly to a WAV file.
    
    Args:
        filename: Output WAV filename
        duration: Recording duration in seconds
        
    Returns:
        True if successful
        
    Example:
        >>> pypac.record_to_file("output.wav", 10)  # Record 10 seconds
        True
    """
    recorder = _get_audio_recorder()
    return recorder.record_to_file(filename, duration)


# Advanced functions

def find_app(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Find an application by name and return its audio session info.
    
    Args:
        app_name: Name or partial name of the application
        
    Returns:
        Session information dictionary, or None if not found
        
    Example:
        >>> info = pypac.find_app("firefox")
        >>> if info:
        ...     print(f"Firefox is {'active' if info['is_active'] else 'inactive'}")
    """
    manager = _get_session_manager()
    return manager.get_session_info(app_name)


def get_active_apps() -> List[str]:
    """
    Get list of applications currently playing audio.
    
    Returns:
        List of application names
        
    Example:
        >>> active_apps = pypac.get_active_apps()
        >>> print(f"Active apps: {', '.join(active_apps)}")
    """
    sessions = list_audio_sessions(active_only=True)
    return [s['process_name'] for s in sessions]


def adjust_volume(app_name: str, delta: float) -> Optional[float]:
    """
    Adjust an application's volume by a delta value.
    
    Args:
        app_name: Name or partial name of the application
        delta: Volume change (-1.0 to 1.0)
        
    Returns:
        New volume level, or None if app not found
        
    Example:
        >>> new_volume = pypac.adjust_volume("spotify", 0.1)  # Increase by 10%
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
        callback: Function called when recording completes (receives audio data)
        
    Example:
        >>> def on_complete(audio_data):
        ...     print(f"Recording complete: {len(audio_data)} samples")
        >>> pypac.record_with_callback(5, on_complete)
    """
    from .recorder import AsyncAudioRecorder
    recorder = AsyncAudioRecorder(callback=callback)
    recorder.start_async(duration)