"""
Native extension wrapper for PyPAC.
This module loads the compiled C++ extensions.
"""

import os
import sys

# Add this directory to path for .pyd loading
_current_dir = os.path.dirname(__file__)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

# Try to import the native extension
try:
    # Try to import from current directory
    from . import pypac as _pypac_module
    SessionEnumerator = _pypac_module.SessionEnumerator
    SimpleLoopback = _pypac_module.SimpleLoopback
except ImportError:
    try:
        # Try direct import
        import pypac as _pypac_module
        SessionEnumerator = _pypac_module.SessionEnumerator
        SimpleLoopback = _pypac_module.SimpleLoopback
    except (ImportError, AttributeError):
        # Try to find .pyd files in dist directory
        _dist_path = os.path.join(os.path.dirname(os.path.dirname(_current_dir)), 'dist')
        if os.path.exists(_dist_path) and _dist_path not in sys.path:
            sys.path.insert(0, _dist_path)
            try:
                import pypac as _pypac_module
                SessionEnumerator = _pypac_module.SessionEnumerator
                SimpleLoopback = _pypac_module.SimpleLoopback
            except ImportError as e:
                raise ImportError(
                    "Failed to load PyPAC native extension. "
                    "Please ensure the module is built: python setup.py build_ext --inplace"
                ) from e

# Export the native classes
__all__ = ['SessionEnumerator', 'SimpleLoopback']