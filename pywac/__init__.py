"""
PyWAC - Python Windows Audio Capture

A high-level Python library for Windows audio capture and control.
Enables process-specific audio recording and volume control.
"""

__version__ = "0.4.0"
__author__ = "PyWAC Contributors"

# Import native extension
import os
import sys
from typing import List, Optional, Dict, Any

# Add _native directory to path for loading .pyd files
_native_path = os.path.join(os.path.dirname(__file__), '_native')
if os.path.exists(_native_path):
    sys.path.insert(0, _native_path)

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
    record_with_callback
)

# Import utils module
from . import utils

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
    
    # Functions - Volume Control
    'set_app_volume',
    'get_app_volume',
    'adjust_volume',
    'mute_app',
    'unmute_app',
    
    # Utilities
    'convert_float32_to_int16',
    'utils'
]