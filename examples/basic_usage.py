#!/usr/bin/env python
"""
PyWAC Basic Usage Example
Demonstrates the core functionality of PyWAC with simple examples
"""

import pywac
import time


def demo_simple_api():
    """Demonstrate simple function API"""
    print("=" * 60)
    print("SIMPLE API DEMO")
    print("=" * 60)
    
    # List all audio sessions
    print("\n1. List audio sessions:")
    sessions = pywac.list_audio_sessions()
    for session in sessions:
        print(f"  - {session['process_name']}: {session['volume_percent']}% "
              f"({'Active' if session['is_active'] else 'Inactive'})")
    
    # Get active sessions
    print("\n2. Active sessions:")
    active_sessions = pywac.get_active_sessions()
    if active_sessions:
        print(f"  Sessions playing audio: {', '.join(active_sessions)}")
    else:
        print("  No sessions currently playing audio")
    
    # Find specific session
    print("\n3. Find Firefox:")
    firefox = pywac.find_audio_session("firefox")
    if firefox:
        print(f"  Found: {firefox['process_name']} - Volume: {firefox['volume_percent']}%")
    else:
        print("  Firefox not found")
    
    # Volume control
    print("\n4. Volume control (if Firefox found):")
    if firefox:
        # Set volume to 50%
        if pywac.set_app_volume("firefox", 0.5):
            print("  Set Firefox volume to 50%")
        
        # Get current volume
        volume = pywac.get_app_volume("firefox")
        if volume is not None:
            print(f"  Current Firefox volume: {volume * 100:.0f}%")
    
    # Record audio (short demo)
    print("\n5. Recording 2 seconds of audio:")
    audio_data = pywac.record_audio(2)
    print(f"  Recorded {audio_data.duration:.1f} seconds ({audio_data.num_frames} frames)")
    
    # Save to file
    print("\n6. Recording to file:")
    if pywac.record_to_file("demo_recording.wav", 2):
        print("  Saved to demo_recording.wav")


def demo_class_api():
    """Demonstrate class-based API"""
    print("\n" + "=" * 60)
    print("CLASS API DEMO")
    print("=" * 60)
    
    # Session Manager
    print("\n1. Using SessionManager:")
    manager = pywac.SessionManager()
    
    # List active sessions
    active_sessions = manager.get_active_sessions()
    print(f"  Found {len(active_sessions)} active sessions")
    
    for session in active_sessions:
        print(f"    - {session}")
    
    # Find and control an app
    print("\n2. Find and control an app:")
    session = manager.find_session("chrome")
    if session:
        print(f"  Found: {session.process_name}")
        print(f"  Current volume: {session.volume * 100:.0f}%")
        
        # Adjust volume
        if manager.set_volume("chrome", 0.7):
            print("  Set Chrome volume to 70%")
    
    # Audio Recorder
    print("\n3. Using AudioRecorder:")
    recorder = pywac.AudioRecorder()
    
    # Start recording
    print("  Starting 3-second recording...")
    recorder.start(duration=3)
    
    # Monitor recording
    while recorder.is_recording:
        print(f"    Recording... {recorder.recording_time:.1f}s "
              f"({recorder.sample_count} samples)", end="\r")
        time.sleep(0.5)
    
    # Stop and get audio
    audio_data = recorder.stop()
    print(f"\n  Recording complete: {audio_data.num_frames} frames ({audio_data.duration:.1f}s)")
    
    # Save to file
    if audio_data.num_frames > 0:
        filename = f"class_demo_{int(time.time())}.wav"
        audio_data.save(filename)
        print(f"  Saved to: {filename}")
    else:
        print("  No audio data to save")


def demo_advanced_features():
    """Demonstrate advanced features"""
    print("\n" + "=" * 60)
    print("ADVANCED FEATURES DEMO")
    print("=" * 60)
    
    # Async recording with callback
    print("\n1. Async recording with callback:")
    
    def on_recording_complete(audio_data):
        print(f"  Callback: Recording complete with {audio_data.duration:.1f} seconds")
    
    pywac.record_with_callback(2, on_recording_complete)
    print("  Recording started asynchronously...")
    time.sleep(2.5)  # Wait for recording to complete
    
    # Volume adjustment
    print("\n2. Adjust volume by delta:")
    result = pywac.adjust_volume("spotify", 0.1)
    if result is not None:
        print(f"  Spotify volume increased to: {result * 100:.0f}%")
    else:
        print("  Spotify not found")
    
    # Utility functions
    print("\n3. Audio data statistics:")
    
    # Load and analyze WAV
    try:
        from pywac.audio_data import AudioData
        audio_data = AudioData.load("demo_recording.wav")
        print(f"  Loaded WAV: {audio_data.num_frames} frames, {audio_data.sample_rate}Hz, {audio_data.channels} channels")
        
        # Get audio statistics
        stats = audio_data.get_statistics()
        
        print(f"  RMS: {stats['rms']:.4f}")
        print(f"  Level: {stats['rms_db']:.1f} dB")
        print(f"  Peak: {stats['peak_db']:.1f} dB")
        print(f"  Duration: {stats['duration']:.2f} seconds")
        
    except FileNotFoundError:
        print("  (demo_recording.wav not found - skipping audio analysis)")


def main():
    print("PyWAC PACKAGE API DEMONSTRATION")
    print("=" * 60)
    print("This demo shows the high-level Python API for PyWAC")
    print()
    
    try:
        # Run demos
        demo_simple_api()
        demo_class_api()
        demo_advanced_features()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nPyWAC provides:")
        print("  - Simple function API for quick tasks")
        print("  - Class-based API for more control")
        print("  - Async recording with callbacks")
        print("  - Audio utilities for WAV processing")
        print("\nInstall with: pip install pywac")
        print("Import with: import pywac")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()