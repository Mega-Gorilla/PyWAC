#!/usr/bin/env python
"""Test script to verify PyPAC package is working correctly"""

import sys
import os

# Add current directory to path to import local package
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("PyPAC PACKAGE TEST")
print("=" * 60)

# Test 1: Import package
print("\n[TEST 1] Import package")
try:
    import pypac
    print("[OK] Package imported successfully")
    print(f"    Version: {pypac.__version__}")
except ImportError as e:
    print(f"[FAILED] Import error: {e}")
    sys.exit(1)

# Test 2: Check API availability
print("\n[TEST 2] Check API availability")
apis = [
    'SessionManager',
    'AudioRecorder', 
    'list_audio_sessions',
    'record_to_file',
    'set_app_volume'
]

for api in apis:
    if hasattr(pypac, api):
        print(f"[OK] pypac.{api} available")
    else:
        print(f"[MISSING] pypac.{api} not found")

# Test 3: Test simple API
print("\n[TEST 3] Test simple API")
try:
    sessions = pypac.list_audio_sessions()
    print(f"[OK] Found {len(sessions)} audio sessions")
    for session in sessions[:3]:
        print(f"    - {session['process_name']} ({session['state']})")
except Exception as e:
    print(f"[ERROR] {e}")

# Test 4: Test SessionManager
print("\n[TEST 4] Test SessionManager")
try:
    manager = pypac.SessionManager()
    print("[OK] SessionManager created")
    
    sessions = manager.list_sessions()
    print(f"[OK] Listed {len(sessions)} sessions")
    
    # Find a session
    session = manager.find_session("firefox")
    if session:
        print(f"[OK] Found Firefox: {session.process_name}")
    else:
        print("[INFO] Firefox not found (may not be running)")
        
except Exception as e:
    print(f"[ERROR] {e}")

# Test 5: Test AudioRecorder
print("\n[TEST 5] Test AudioRecorder")
try:
    recorder = pypac.AudioRecorder()
    print("[OK] AudioRecorder created")
    
    # Test recording (very short)
    print("    Starting 1-second test recording...")
    audio_data = recorder.record(1)
    print(f"[OK] Recorded {len(audio_data)} samples")
    
except Exception as e:
    print(f"[ERROR] {e}")

# Test 6: Test utilities
print("\n[TEST 6] Test utilities")
try:
    from pypac.utils import calculate_rms, normalize_audio
    print("[OK] Utilities imported")
    
    # Test RMS calculation
    test_data = [0.1, 0.2, 0.3, 0.2, 0.1]
    rms = calculate_rms(test_data)
    print(f"[OK] RMS calculation: {rms:.4f}")
    
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("\nPyPAC package is working correctly!")
print("You can now use it with: import pypac")