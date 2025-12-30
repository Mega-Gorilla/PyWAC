"""
PyWAC - Python Windows Audio Capture

A high-level Python library for Windows audio capture and control.
Enables process-specific audio recording and volume control.
"""

__version__ = "1.0.0"
__author__ = "PyWAC Contributors"

from typing import List, Optional, Dict, Any

# Import core components
from .sessions import SessionManager, AudioSession
from .recorder import AudioRecorder, AsyncAudioRecorder
from .audio_data import AudioData
from .utils import convert_float32_to_int16

# Convenience functions
from .api import (
    list_audio_sessions,
    record_to_file,
    record_audio,
    record_process,
    record_process_id,
    list_recordable_processes,
    set_app_volume,
    get_app_volume,
    mute_app,
    unmute_app,
    find_app,
    find_audio_session,
    get_active_apps,
    get_active_sessions,
    adjust_volume,
    record_with_callback,
    refresh_sessions,
)

# Import utils module
from . import utils

# Import native modules as public API
# These are low-level but stable APIs for advanced users
try:
    from . import core  # Session enumeration and system loopback
    from . import capture  # Process-specific audio capture
except ImportError:
    # Native extensions not built yet
    core = None  # type: ignore
    capture = None  # type: ignore

# Public API
__all__ = [
    # Version
    '__version__',

    # Classes
    'SessionManager',
    'AudioSession',
    'AudioRecorder',
    'AsyncAudioRecorder',
    'AudioData',

    # Functions - Audio Recording
    'record_to_file',
    'record_audio',
    'record_process',
    'record_process_id',
    'record_with_callback',

    # Functions - Session Management
    'list_audio_sessions',
    'list_recordable_processes',
    'find_audio_session',
    'find_app',  # Deprecated
    'get_active_sessions',
    'get_active_apps',  # Deprecated
    'refresh_sessions',

    # Functions - Volume Control
    'set_app_volume',
    'get_app_volume',
    'adjust_volume',
    'mute_app',
    'unmute_app',

    # Utilities
    'convert_float32_to_int16',
    'utils',

    # Low-level native modules (public API)
    'core',
    'capture',
]