"""
Tests for PyWAC import structure and module naming (v1.0.0).

These tests verify that the new module structure works correctly:
- pywac.core: Session enumeration and system loopback
- pywac.capture: Process-specific audio capture
"""

import pytest
import threading


# Check if native extensions are available
def _native_available():
    try:
        from pywac import core, capture
        return core is not None and capture is not None
    except ImportError:
        return False


requires_native = pytest.mark.skipif(
    not _native_available(),
    reason="Native extensions not built. Run: python setup.py build_ext --inplace"
)


@requires_native
def test_import_pywac():
    """Test that pywac can be imported cleanly."""
    import pywac
    assert hasattr(pywac, 'record_to_file')
    assert hasattr(pywac, 'SessionManager')
    assert hasattr(pywac, '__version__')
    assert pywac.__version__ == "1.0.0"


@requires_native
def test_core_module_import():
    """Test that pywac.core is accessible as public API."""
    from pywac import core
    assert hasattr(core, 'SessionEnumerator')
    assert hasattr(core, 'SimpleLoopback')
    assert hasattr(core, 'SessionState')


@requires_native
def test_capture_module_import():
    """Test that pywac.capture is accessible as public API."""
    from pywac import capture
    assert hasattr(capture, 'QueueBasedProcessCapture')
    assert hasattr(capture, 'list_audio_processes')


@requires_native
def test_low_level_api_usage():
    """Test that low-level APIs work correctly."""
    from pywac.core import SessionEnumerator
    from pywac.capture import QueueBasedProcessCapture

    # Session enumeration
    enumerator = SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    assert isinstance(sessions, list)

    # Capture instance creation
    cap = QueueBasedProcessCapture()
    assert cap is not None


@requires_native
def test_deprecated_function_warning():
    """Test that deprecated functions emit warnings."""
    import warnings
    import pywac

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pywac.find_app("nonexistent_test_app")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "find_audio_session" in str(w[0].message)


@requires_native
def test_deprecated_get_active_apps_warning():
    """Test that get_active_apps() emits deprecation warning."""
    import warnings
    import pywac

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        pywac.get_active_apps()
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "get_active_sessions" in str(w[0].message)


@requires_native
def test_thread_safety():
    """Test that global singletons are thread-safe."""
    from pywac import api

    results = []

    def get_manager():
        results.append(id(api._get_session_manager()))

    threads = [threading.Thread(target=get_manager) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All threads should get the same instance
    assert len(set(results)) == 1


@requires_native
def test_refresh_sessions():
    """Test that refresh_sessions() is exposed as public API."""
    import pywac
    assert hasattr(pywac, 'refresh_sessions')
    # Should not raise
    pywac.refresh_sessions()


@requires_native
def test_public_api_exports():
    """Test that all expected APIs are exported from pywac."""
    import pywac

    # Classes
    assert hasattr(pywac, 'SessionManager')
    assert hasattr(pywac, 'AudioSession')
    assert hasattr(pywac, 'AudioRecorder')
    assert hasattr(pywac, 'AsyncAudioRecorder')
    assert hasattr(pywac, 'AudioData')

    # Recording functions
    assert hasattr(pywac, 'record_to_file')
    assert hasattr(pywac, 'record_audio')
    assert hasattr(pywac, 'record_process')
    assert hasattr(pywac, 'record_process_id')
    assert hasattr(pywac, 'record_with_callback')

    # Session management
    assert hasattr(pywac, 'list_audio_sessions')
    assert hasattr(pywac, 'list_recordable_processes')
    assert hasattr(pywac, 'find_audio_session')
    assert hasattr(pywac, 'get_active_sessions')
    assert hasattr(pywac, 'refresh_sessions')

    # Volume control
    assert hasattr(pywac, 'set_app_volume')
    assert hasattr(pywac, 'get_app_volume')
    assert hasattr(pywac, 'adjust_volume')
    assert hasattr(pywac, 'mute_app')
    assert hasattr(pywac, 'unmute_app')

    # Native modules
    assert hasattr(pywac, 'core')
    assert hasattr(pywac, 'capture')


@requires_native
def test_core_direct_import():
    """Test direct import from pywac.core."""
    from pywac.core import SessionEnumerator, SimpleLoopback

    # These should be the actual classes, not None
    assert SessionEnumerator is not None
    assert SimpleLoopback is not None


@requires_native
def test_capture_direct_import():
    """Test direct import from pywac.capture."""
    from pywac.capture import QueueBasedProcessCapture

    # This should be the actual class, not None
    assert QueueBasedProcessCapture is not None
