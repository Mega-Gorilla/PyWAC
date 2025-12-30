"""
Audio session management module for PyWAC.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pywac import core as _native  # Native extension: session enumeration and system loopback


@dataclass
class AudioSession:
    """Represents an audio session for a Windows process."""
    
    process_id: int
    process_name: str
    display_name: str
    state: int  # 0: Inactive, 1: Active, 2: Expired
    volume: float  # 0.0 to 1.0
    muted: bool
    
    @property
    def is_active(self) -> bool:
        """Check if the session is actively playing audio."""
        return self.state == 1
    
    @property
    def is_muted(self) -> bool:
        """Check if the session is muted."""
        return self.muted
    
    @property
    def state_name(self) -> str:
        """Get human-readable state name."""
        states = {0: "Inactive", 1: "Active", 2: "Expired"}
        return states.get(self.state, "Unknown")
    
    def __str__(self) -> str:
        """String representation of the session."""
        mute_str = "Muted" if self.muted else f"Volume: {self.volume:.0%}"
        return f"{self.process_name} (PID: {self.process_id}) - {self.state_name} - {mute_str}"


class SessionManager:
    """High-level interface for managing audio sessions."""
    
    def __init__(self):
        """Initialize the session manager."""
        try:
            self._enumerator = _native.SessionEnumerator()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize SessionManager: {e}")
    
    def list_sessions(self, active_only: bool = False) -> List[AudioSession]:
        """
        List all audio sessions.
        
        Args:
            active_only: If True, only return active sessions
            
        Returns:
            List of AudioSession objects
        """
        try:
            raw_sessions = self._enumerator.enumerate_sessions()
        except Exception as e:
            raise RuntimeError(f"Failed to enumerate sessions: {e}")
        
        sessions = []
        for raw in raw_sessions:
            session = AudioSession(
                process_id=raw.process_id,
                process_name=raw.process_name,
                display_name=raw.display_name if hasattr(raw, 'display_name') else '',
                state=raw.state,
                volume=raw.volume,
                muted=raw.muted
            )
            
            if not active_only or session.is_active:
                sessions.append(session)
        
        return sessions
    
    def find_session(self, app_name: str) -> Optional[AudioSession]:
        """
        Find a session by application name (case-insensitive partial match).
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            First matching AudioSession, or None if not found
        """
        app_name_lower = app_name.lower()
        sessions = self.list_sessions()
        
        for session in sessions:
            if app_name_lower in session.process_name.lower():
                return session
        
        return None
    
    def set_volume(self, app_name: str, volume: float) -> bool:
        """
        Set the volume for an application.
        
        Args:
            app_name: Name or partial name of the application
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        if not 0.0 <= volume <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        
        session = self.find_session(app_name)
        if not session:
            return False
        
        try:
            return self._enumerator.set_session_volume(session.process_id, volume)
        except Exception as e:
            raise RuntimeError(f"Failed to set volume: {e}")
    
    def get_volume(self, app_name: str) -> Optional[float]:
        """
        Get the current volume for an application.
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            Volume level (0.0 to 1.0), or None if app not found
        """
        session = self.find_session(app_name)
        return session.volume if session else None
    
    def set_mute(self, app_name: str, mute: bool) -> bool:
        """
        Set the mute state for an application.
        
        Args:
            app_name: Name or partial name of the application
            mute: True to mute, False to unmute
            
        Returns:
            True if successful, False otherwise
        """
        session = self.find_session(app_name)
        if not session:
            return False
        
        try:
            # Check if set_session_mute method exists
            if hasattr(self._enumerator, 'set_session_mute'):
                return self._enumerator.set_session_mute(session.process_id, mute)
            else:
                # Fallback: mute by setting volume to 0
                if mute:
                    return self._enumerator.set_session_volume(session.process_id, 0.0)
                else:
                    # Can't unmute without knowing previous volume
                    return False
        except Exception as e:
            raise RuntimeError(f"Failed to set mute state: {e}")
    
    def is_muted(self, app_name: str) -> Optional[bool]:
        """
        Check if an application is muted.
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            True if muted, False if not, None if app not found
        """
        session = self.find_session(app_name)
        return session.muted if session else None
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of process names currently playing audio.
        
        Returns:
            List of process names with active sessions
        """
        sessions = self.list_sessions(active_only=True)
        return [s.process_name for s in sessions]
    
    def get_active_session_objects(self) -> List[AudioSession]:
        """
        Get all active audio session objects.
        
        Returns:
            List of AudioSession objects for active sessions
        """
        return self.list_sessions(active_only=True)
    
    def get_session_info(self, app_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a session.
        
        Args:
            app_name: Name or partial name of the application
            
        Returns:
            Dictionary with session information, or None if not found
        """
        session = self.find_session(app_name)
        if not session:
            return None
        
        return {
            'process_id': session.process_id,
            'process_name': session.process_name,
            'display_name': session.display_name,
            'state': session.state_name,
            'is_active': session.is_active,
            'volume': session.volume,
            'volume_percent': int(session.volume * 100),
            'is_muted': session.muted
        }