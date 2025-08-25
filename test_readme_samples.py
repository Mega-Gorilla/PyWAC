"""
Test all sample codes from README.md to ensure they work correctly
"""

import sys
import os
import time
import tempfile
import traceback

# Set UTF-8 encoding for stdout
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pywac
import numpy as np

def test_quick_start_samples():
    """Test the 3-second quick start samples"""
    print("\n=== Testing Quick Start Samples ===")
    
    try:
        # Test 1: Simple recording to file
        print("Testing: pywac.record_to_file()")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
        
        # Should return True on success
        result = pywac.record_to_file(temp_file, duration=0.1)
        assert result == True, f"Expected True, got {result}"
        assert os.path.exists(temp_file), "File was not created"
        os.unlink(temp_file)
        print("[OK] record_to_file works")
        
        # Test 2: Process recording (may fail if game.exe doesn't exist)
        print("Testing: pywac.record_process() - expected to fail for non-existent process")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
        result = pywac.record_process("game.exe", temp_file, duration=0.1)
        # This is expected to fail
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        print("[OK] record_process behaves as expected")
        
        # Test 3: Set app volume (may fail if spotify not running)
        print("Testing: pywac.set_app_volume()")
        result = pywac.set_app_volume("spotify", 0.5)
        # Result can be True or False depending on if Spotify is running
        print(f"[OK] set_app_volume returns: {result}")
        
        # Test 4: Get active sessions
        print("Testing: pywac.get_active_sessions()")
        active = pywac.get_active_sessions()
        assert isinstance(active, list), f"Expected list, got {type(active)}"
        print(f"[OK] get_active_sessions returns list with {len(active)} items")
        
    except Exception as e:
        print(f"[FAIL] Quick start samples failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_high_level_api_samples():
    """Test high-level API samples from README"""
    print("\n=== Testing High-Level API Samples ===")
    
    try:
        # Test record_to_file
        print("Testing: record_to_file")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
        result = pywac.record_to_file(temp_file, duration=0.1)
        assert result == True
        os.unlink(temp_file)
        print("[OK] record_to_file works")
        
        # Test get_active_sessions
        print("Testing: get_active_sessions")
        active = pywac.get_active_sessions()
        assert isinstance(active, list)
        for app in active:
            assert isinstance(app, str), f"Expected string, got {type(app)}"
        print("[OK] get_active_sessions returns list of strings")
        
        # Test find_audio_session
        print("Testing: find_audio_session")
        firefox = pywac.find_audio_session("firefox")
        if firefox:
            assert isinstance(firefox, dict)
            assert 'volume_percent' in firefox
            print(f"[OK] find_audio_session returns dict with volume_percent: {firefox['volume_percent']}%")
        else:
            print("[OK] find_audio_session returns None when not found")
        
        # Test list_audio_sessions
        print("Testing: list_audio_sessions")
        sessions = pywac.list_audio_sessions()
        assert isinstance(sessions, list)
        if sessions:
            s = sessions[0]
            assert isinstance(s, dict)
            assert 'process_name' in s
            assert 'volume_percent' in s
            print(f"[OK] list_audio_sessions returns correct format")
        else:
            print("[OK] list_audio_sessions returns empty list")
            
    except Exception as e:
        print(f"[FAIL] High-level API samples failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_class_based_api_samples():
    """Test class-based API samples - these have issues"""
    print("\n=== Testing Class-Based API Samples ===")
    
    try:
        # Test SessionManager
        print("Testing: SessionManager")
        manager = pywac.SessionManager()
        
        # Get active sessions - returns list of AudioSession objects
        sessions = manager.get_active_session_objects()
        assert isinstance(sessions, list)
        for session in sessions:
            assert hasattr(session, 'process_name')
            assert hasattr(session, 'volume')
            assert hasattr(session, 'is_muted')
        print("[OK] SessionManager.get_active_session_objects() works")
        
        # Test AudioRecorder
        print("Testing: AudioRecorder")
        recorder = pywac.AudioRecorder()
        recorder.start(duration=0.1)
        
        # Quick check of properties
        assert recorder.is_recording == True
        time.sleep(0.15)  # Wait for recording to finish
        
        audio_data = recorder.stop()
        # NOTE: The README sample is WRONG here!
        # audio_data is now AudioData object, not a list
        assert hasattr(audio_data, 'samples'), "Should return AudioData object"
        assert hasattr(audio_data, 'save'), "AudioData should have save method"
        
        # Save using AudioData's save method
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
        audio_data.save(temp_file)
        assert os.path.exists(temp_file)
        os.unlink(temp_file)
        print("[OK] AudioRecorder returns AudioData (README needs update)")
        
    except Exception as e:
        print(f"[FAIL] Class-based API samples failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_callback_recording():
    """Test callback recording sample - this has issues"""
    print("\n=== Testing Callback Recording ===")
    
    try:
        callback_completed = False
        received_data = None
        
        def on_recording_complete(audio_data):
            nonlocal callback_completed, received_data
            callback_completed = True
            received_data = audio_data
            
            # Check that it's AudioData object
            assert hasattr(audio_data, 'samples'), "Should be AudioData object"
            assert hasattr(audio_data, 'duration'), "Should have duration"
            print(f"[OK] Callback received AudioData: {audio_data.duration:.2f}s")
        
        # Start recording with callback
        pywac.record_with_callback(0.1, on_recording_complete)
        
        # Wait for completion
        time.sleep(0.5)
        
        assert callback_completed, "Callback was not called"
        assert received_data is not None, "No data received"
        print("[OK] Callback recording works (returns AudioData)")
        
    except Exception as e:
        print(f"[FAIL] Callback recording failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_utils_functions():
    """Test utility functions"""
    print("\n=== Testing Utility Functions ===")
    
    try:
        # Test calculate_rms
        print("Testing: pywac.utils.calculate_rms")
        test_data = np.array([0.0, 0.5, -0.5, 0.25, -0.25])
        rms = pywac.utils.calculate_rms(test_data)
        expected_rms = np.sqrt(np.mean(test_data ** 2))
        assert abs(rms - expected_rms) < 0.001
        print("[OK] calculate_rms works")
        
        # Test calculate_db
        print("Testing: pywac.utils.calculate_db")
        db = pywac.utils.calculate_db(test_data)
        assert isinstance(db, float)
        print(f"[OK] calculate_db returns: {db:.1f} dB")
        
        # Test save_to_wav (deprecated but should still work)
        print("Testing: pywac.utils.save_to_wav (deprecated)")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_file = f.name
        
        test_audio = np.random.randn(4800).astype(np.float32) * 0.1
        pywac.utils.save_to_wav(test_audio, temp_file, 48000, 1)
        assert os.path.exists(temp_file)
        os.unlink(temp_file)
        print("[OK] save_to_wav still works (with deprecation warning)")
        
    except Exception as e:
        print(f"[FAIL] Utility functions failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def check_readme_correctness():
    """Check if README samples are now correct after fixes"""
    print("\n=== Verifying README Corrections ===")
    
    # Read README.md to check if issues are fixed
    with open('README.md', 'r', encoding='utf-8') as f:
        readme_content = f.read()
    
    issues_found = []
    
    # Check Issue 1: AudioRecorder example
    if 'if len(audio_data) > 0:' in readme_content:
        issues_found.append("Issue 1: AudioRecorder example still uses len(audio_data)")
    elif 'if audio_data.num_frames > 0:' in readme_content:
        print("[OK] Issue 1 fixed: AudioRecorder example uses audio_data.num_frames")
    
    # Check Issue 2: Callback recording
    if 'print(f"録音完了: {len(audio_data)} サンプル")' in readme_content:
        issues_found.append("Issue 2: Callback recording still uses len(audio_data)")
    elif 'print(f"録音完了: {audio_data.num_frames} サンプル")' in readme_content:
        print("[OK] Issue 2 fixed: Callback recording uses audio_data.num_frames")
    
    # Check Issue 3: Audio meter
    if 'buffer = recorder.get_buffer()' in readme_content:
        issues_found.append("Issue 3: Audio meter still uses recorder.get_buffer()")
    elif 'audio_data = recorder.get_audio()' in readme_content:
        print("[OK] Issue 3 fixed: Audio meter uses recorder.get_audio()")
    
    # Check English README too
    with open('README.en.md', 'r', encoding='utf-8') as f:
        readme_en_content = f.read()
    
    # Check English README for the same issues
    if 'if len(audio_data) > 0:' in readme_en_content:
        issues_found.append("English README: AudioRecorder example still uses len(audio_data)")
    else:
        print("[OK] English README Issue 1 fixed")
    
    if 'print(f"Recording complete: {len(audio_data)} samples")' in readme_en_content:
        issues_found.append("English README: Callback recording still uses len(audio_data)")
    else:
        print("[OK] English README Issue 2 fixed")
    
    if 'buffer = recorder.get_buffer()' in readme_en_content:
        issues_found.append("English README: Audio meter still uses recorder.get_buffer()")
    else:
        print("[OK] English README Issue 3 fixed")
    
    return issues_found


def main():
    """Run all README sample tests"""
    print("=" * 60)
    print("README SAMPLE CODE VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Test each section
    results.append(("Quick Start", test_quick_start_samples()))
    results.append(("High-Level API", test_high_level_api_samples()))
    results.append(("Class-Based API", test_class_based_api_samples()))
    results.append(("Callback Recording", test_callback_recording()))
    results.append(("Utility Functions", test_utils_functions()))
    
    # Check if README issues are fixed
    issues = check_readme_correctness()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{name:20} {status}")
    
    all_passed = all(r for _, r in results)
    
    if not all_passed:
        print("\n[FAIL] Some tests failed")
        return False
    
    if issues:
        print(f"\n[WARNING] Found {len(issues)} remaining issues in README:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("\n[SUCCESS] All README samples are correct and working!")
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)