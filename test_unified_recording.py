#!/usr/bin/env python
"""Test unified recording implementation (v0.4.2)"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

import pywac
from pywac.unified_recording import record, Recorder, capture_system_audio, capture_app_audio

def test_unified_api():
    """Test the new unified recording API"""
    
    print("Testing Unified Recording API (v0.4.2)")
    print("=" * 60)
    
    # Test 1: System recording (synchronous)
    print("\n1. Testing system recording (sync)...")
    try:
        audio = record(duration=1.0, target=None)
        if audio and audio.num_frames > 0:
            print(f"   [OK] Recorded {audio.duration:.1f}s of system audio")
        else:
            print("   [WARNING] No audio data captured")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 2: Process recording by name
    print("\n2. Testing process recording by name...")
    try:
        # Find active process
        sessions = pywac.list_audio_sessions(active_only=True)
        if sessions:
            process_name = sessions[0]['process_name']
            print(f"   Target: {process_name}")
            
            audio = record(duration=1.0, target=process_name)
            if audio and audio.num_frames > 0:
                print(f"   [OK] Recorded {audio.duration:.1f}s from {process_name}")
            else:
                print("   [WARNING] No audio data captured")
        else:
            print("   [SKIP] No active audio sessions")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 3: File output
    print("\n3. Testing direct file output...")
    try:
        test_file = "test_unified_output.wav"
        success = record(duration=1.0, target=None, output_file=test_file)
        if success:
            if os.path.exists(test_file):
                size = os.path.getsize(test_file) / 1024
                print(f"   [OK] Saved to {test_file} ({size:.1f} KB)")
                os.remove(test_file)
            else:
                print("   [ERROR] File not created")
        else:
            print("   [ERROR] Recording failed")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 4: Async recording with callback
    print("\n4. Testing async recording with callback...")
    callback_results = []
    
    def on_recording_complete(audio_data):
        callback_results.append(audio_data)
        print(f"   [CALLBACK] Received {audio_data.duration:.1f}s of audio")
    
    try:
        result = record(duration=1.0, target=None, on_complete=on_recording_complete)
        if result is None:
            print("   [OK] Async recording started")
            # Wait for callback
            time.sleep(1.5)
            if callback_results:
                print("   [OK] Callback executed successfully")
            else:
                print("   [WARNING] Callback not executed")
        else:
            print("   [ERROR] Should return None for async")
    except Exception as e:
        print(f"   [ERROR] {e}")


def test_recorder_class():
    """Test the Recorder class interface"""
    
    print("\n\nTesting Recorder Class Interface")
    print("=" * 60)
    
    # Test 1: System recorder
    print("\n1. Testing system Recorder...")
    try:
        recorder = Recorder(target=None)
        if recorder.is_available():
            audio = recorder.record(0.5)
            if audio and audio.num_frames > 0:
                print(f"   [OK] System recorder: {audio.duration:.1f}s")
            else:
                print("   [WARNING] No audio captured")
        else:
            print("   [ERROR] System recorder not available")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 2: Process recorder by name
    print("\n2. Testing process Recorder...")
    sessions = pywac.list_audio_sessions(active_only=True)
    if sessions:
        process_name = sessions[0]['process_name']
        try:
            recorder = Recorder(target=process_name)
            if recorder.is_available():
                success = recorder.record_to_file(0.5, "test_recorder.wav")
                if success and os.path.exists("test_recorder.wav"):
                    size = os.path.getsize("test_recorder.wav") / 1024
                    print(f"   [OK] Process recorder: saved {size:.1f} KB")
                    os.remove("test_recorder.wav")
                else:
                    print("   [ERROR] Recording failed")
            else:
                print(f"   [WARNING] {process_name} not available")
        except Exception as e:
            print(f"   [ERROR] {e}")
    else:
        print("   [SKIP] No active sessions")
    
    # Test 3: Async recording
    print("\n3. Testing async Recorder...")
    async_results = []
    
    def handle_async(audio):
        async_results.append(audio)
        print(f"   [ASYNC] Got {audio.duration:.1f}s")
    
    try:
        recorder = Recorder()
        recorder.record_async(0.5, handle_async)
        print("   [OK] Async started")
        time.sleep(1.0)
        if async_results:
            print("   [OK] Async completed")
        else:
            print("   [WARNING] Async callback not executed")
    except Exception as e:
        print(f"   [ERROR] {e}")


def test_convenience_functions():
    """Test convenience functions"""
    
    print("\n\nTesting Convenience Functions")
    print("=" * 60)
    
    # Test 1: capture_system_audio
    print("\n1. Testing capture_system_audio...")
    try:
        audio = capture_system_audio(0.5)
        if audio and audio.num_frames > 0:
            print(f"   [OK] Captured {audio.duration:.1f}s system audio")
        else:
            print("   [WARNING] No audio captured")
    except Exception as e:
        print(f"   [ERROR] {e}")
    
    # Test 2: capture_app_audio
    sessions = pywac.list_audio_sessions(active_only=True)
    if sessions:
        app_name = sessions[0]['process_name'].replace('.exe', '')
        print(f"\n2. Testing capture_app_audio ('{app_name}')...")
        try:
            audio = capture_app_audio(app_name, 0.5)
            if audio and audio.num_frames > 0:
                print(f"   [OK] Captured {audio.duration:.1f}s from {app_name}")
            else:
                print("   [WARNING] No audio captured")
        except Exception as e:
            print(f"   [ERROR] {e}")
    else:
        print("\n2. [SKIP] No active apps for capture_app_audio test")


def test_backward_compatibility():
    """Test that old API still works"""
    
    print("\n\nTesting Backward Compatibility")
    print("=" * 60)
    
    # Test original APIs
    tests = [
        ("record_audio", lambda: pywac.record_audio(0.5)),
        ("record_to_file", lambda: pywac.record_to_file("test_compat.wav", 0.5)),
        ("record_with_callback", lambda: pywac.record_with_callback(0.5, lambda x: None)),
    ]
    
    for name, func in tests:
        print(f"\n{name}...")
        try:
            result = func()
            if name == "record_audio":
                if result and result.num_frames > 0:
                    print(f"   [OK] {name} works")
                else:
                    print(f"   [WARNING] {name} returned no data")
            elif name == "record_to_file":
                if os.path.exists("test_compat.wav"):
                    print(f"   [OK] {name} works")
                    os.remove("test_compat.wav")
                else:
                    print(f"   [WARNING] {name} file not created")
            else:
                print(f"   [OK] {name} executed")
        except Exception as e:
            print(f"   [ERROR] {name}: {e}")
    
    # Test process recording
    sessions = pywac.list_audio_sessions(active_only=True)
    if sessions:
        process = sessions[0]['process_name']
        pid = sessions[0]['process_id']
        
        print(f"\nrecord_process ('{process}')...")
        try:
            success = pywac.record_process(process, "test_process.wav", 0.5)
            if success and os.path.exists("test_process.wav"):
                print("   [OK] record_process works")
                os.remove("test_process.wav")
            else:
                print("   [WARNING] record_process failed")
        except Exception as e:
            print(f"   [ERROR] {e}")
        
        print(f"\nrecord_process_id ({pid})...")
        try:
            success = pywac.record_process_id(pid, "test_pid.wav", 0.5)
            if success and os.path.exists("test_pid.wav"):
                print("   [OK] record_process_id works")
                os.remove("test_pid.wav")
            else:
                print("   [WARNING] record_process_id failed")
        except Exception as e:
            print(f"   [ERROR] {e}")


def main():
    """Run all tests"""
    
    print("=" * 60)
    print("PyWAC Unified Recording Test Suite (v0.4.2)")
    print("=" * 60)
    
    test_unified_api()
    test_recorder_class()
    test_convenience_functions()
    test_backward_compatibility()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Clean up any remaining test files
    for filename in ["test_unified_output.wav", "test_recorder.wav", 
                     "test_compat.wav", "test_process.wav", "test_pid.wav"]:
        if os.path.exists(filename):
            os.remove(filename)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())