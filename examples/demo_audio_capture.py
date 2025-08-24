"""
PyPAC Audio Capture Demo - Demonstrates all main features using package API
Shows audio session enumeration, audio recording, and volume control
"""

import pypac
import time
import sys

# Import numpy with error handling
try:
    import numpy as np
except ImportError:
    print("Warning: NumPy not installed. Some features will be limited.")
    print("Install with: pip install numpy")
    np = None


def example_enumerate_sessions():
    """Example: Enumerate all audio sessions using high-level API"""
    print("=" * 60)
    print("EXAMPLE 1: Enumerate Audio Sessions")
    print("=" * 60)
    
    try:
        # Use high-level API to list sessions
        sessions = pypac.list_audio_sessions()
    except Exception as e:
        print(f"Error listing sessions: {e}")
        print("Make sure you have proper permissions.")
        return
    
    print(f"\nFound {len(sessions)} audio sessions:\n")
    
    for session in sessions:
        state = "Active" if session['is_active'] else "Inactive"
        
        print(f"Process: {session['process_name']} (PID: {session['process_id']})")
        print(f"  State: {state}")
        print(f"  Volume: {session['volume_percent']:.0f}%")
        print(f"  Muted: {'Yes' if session['is_muted'] else 'No'}")
        print()
    
    # Show active apps
    active_apps = pypac.get_active_apps()
    if active_apps:
        print(f"Active applications: {', '.join(active_apps)}")
    else:
        print("No applications currently playing audio")


def example_simple_capture():
    """Example: Simple audio recording using AudioRecorder"""
    print("=" * 60)
    print("EXAMPLE 2: Audio Recording")
    print("=" * 60)
    
    if np is None:
        print("Skipping detailed audio analysis (NumPy not installed)")
        # Still do basic recording
        print("\nRecording 3 seconds of audio...")
        audio_data = pypac.record_audio(3)
        print(f"Recorded {len(audio_data)} samples")
        
        # Save to file
        if pypac.record_to_file("demo_capture.wav", 2):
            print("Saved 2-second recording to demo_capture.wav")
        return
    
    try:
        # Create AudioRecorder instance
        recorder = pypac.AudioRecorder()
    except Exception as e:
        print(f"Error creating AudioRecorder: {e}")
        return
    
    print("\nStarting audio capture...")
    print("Recording for 3 seconds...")
    print("Please play some audio...\n")
    
    # Start recording
    recorder.start(duration=3)
    
    # Monitor recording progress
    while recorder.is_recording:
        time.sleep(1)
        current_time = recorder.recording_time
        samples = recorder.sample_count
        
        if samples > 0 and np is not None:
            # Get current buffer for analysis
            buffer = recorder.get_buffer()
            if len(buffer) > 0:
                # Calculate RMS (Root Mean Square) for volume indication
                rms = np.sqrt(np.mean(np.array(buffer)**2))
                db = 20 * np.log10(rms + 1e-10)
                
                # Create simple VU meter
                meter_width = 30
                normalized = min(1.0, max(0.0, (db + 60) / 60))  # Normalize -60dB to 0dB
                filled = int(normalized * meter_width)
                meter = "█" * filled + "░" * (meter_width - filled)
                
                print(f"  [{current_time:.0f}s] {meter} {samples:6d} samples | {db:+6.1f} dB")
        else:
            print(f"  [{current_time:.0f}s] {'░' * 30} Recording...")
    
    # Get final audio data
    audio_data = recorder.stop()
    print(f"\nCapture stopped. Total samples: {len(audio_data):,}")
    
    # Save to file
    filename = recorder.save("demo_capture.wav")
    if filename:
        print(f"Saved recording to: {filename}")


def example_volume_control():
    """Example: Control volume of specific process using high-level API"""
    print("=" * 60)
    print("EXAMPLE 3: Volume Control")
    print("=" * 60)
    
    try:
        # Get active apps
        active_apps = pypac.get_active_apps()
    except Exception as e:
        print(f"Error: {e}")
        return
    
    if not active_apps:
        print("\nNo active audio sessions found.")
        print("Please play some audio and try again.")
        return
    
    # Use first active app as example
    target_app = active_apps[0]
    
    print(f"\nTarget application: {target_app}")
    
    # Get current volume
    current_volume = pypac.get_app_volume(target_app)
    if current_volume is not None:
        print(f"Current volume: {current_volume * 100:.0f}%")
    
    # Set volume to 50%
    new_volume = 0.5
    print(f"Setting volume to {new_volume * 100:.0f}%...")
    
    if pypac.set_app_volume(target_app, new_volume):
        print("Volume changed successfully!")
        
        # Verify the change
        verified_volume = pypac.get_app_volume(target_app)
        if verified_volume is not None:
            print(f"Verified new volume: {verified_volume * 100:.0f}%")
    else:
        print("Failed to change volume.")
    
    # Demonstrate volume adjustment
    print("\nAdjusting volume by +10%...")
    adjusted = pypac.adjust_volume(target_app, 0.1)
    if adjusted is not None:
        print(f"New volume after adjustment: {adjusted * 100:.0f}%")


def example_session_manager():
    """Example: Using SessionManager class for advanced control"""
    print("=" * 60)
    print("EXAMPLE 4: SessionManager Class")
    print("=" * 60)
    
    # Create session manager
    manager = pypac.SessionManager()
    
    # Get active sessions
    active_sessions = manager.get_active_sessions()
    print(f"\nFound {len(active_sessions)} active sessions")
    
    # Find specific application
    print("\nSearching for browser sessions...")
    for browser in ["firefox", "chrome", "edge", "brave"]:
        session = manager.find_session(browser)
        if session:
            print(f"Found {session.process_name}:")
            print(f"  PID: {session.process_id}")
            print(f"  Volume: {session.volume * 100:.0f}%")
            print(f"  State: {session.state}")
            break
    else:
        print("No browser sessions found")


def main():
    print("PyPAC - PYTHON PROCESS AUDIO CAPTURE EXAMPLES")
    print("=" * 60)
    print(f"Version: {pypac.__version__}")
    print()
    
    # Check if running as admin
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Running as Administrator: {'Yes' if is_admin else 'No'}")
        if not is_admin:
            print("Note: Some features may require administrator privileges.")
    except Exception as e:
        print(f"Could not check admin status: {e}")
    
    print()
    
    # Run examples
    example_enumerate_sessions()
    print()
    example_simple_capture()
    print()
    example_volume_control()
    print()
    example_session_manager()
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)
    print("\nFor more examples, see package_demo.py")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Failed to import pypac module")
        print("=" * 60)
        print(f"Details: {e}")
        print("\nPlease install the package:")
        print("  pip install -e .")
        print("\nOr build the module:")
        print("  python setup.py build_ext --inplace")
        sys.exit(1)