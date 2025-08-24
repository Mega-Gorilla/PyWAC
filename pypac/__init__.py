"""
PyPAC - Python Process Audio Capture for Windows

A high-level Python library for Windows audio capture and control.
"""

__version__ = "0.2.0"
__author__ = "PyPAC Contributors"

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
from .recorder import AudioRecorder
from .utils import save_to_wav, convert_float32_to_int16

# Convenience functions
from .api import (
    list_audio_sessions,
    record_to_file,
    record_audio,
    set_app_volume,
    get_app_volume,
    mute_app,
    unmute_app,
    find_app,
    get_active_apps,
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
    
    # Functions
    'list_audio_sessions',
    'record_to_file',
    'record_audio',
    'set_app_volume',
    'get_app_volume',
    'mute_app',
    'unmute_app',
    'find_app',
    'get_active_apps',
    'adjust_volume',
    'record_with_callback',
    
    # Utilities
    'save_to_wav',
    'convert_float32_to_int16',
    'utils'
]