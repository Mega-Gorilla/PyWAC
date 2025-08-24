"""
PyPAC Audio Capture Demo - Demonstrates all main features
Shows audio session enumeration, system capture, and volume control
"""

import sys
import os
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dist'))

# Error handling for module import
try:
    import pypac
except ImportError as e:
    print("=" * 60)
    print("ERROR: Failed to import pypac module")
    print("=" * 60)
    print(f"Details: {e}")
    print("\nPossible solutions:")
    print("1. Build the module: python setup.py build_ext --inplace")
    print("2. Install Visual C++ Redistributable from:")
    print("   https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("3. Check if pypac.pyd exists in dist/ folder")
    sys.exit(1)

# Import numpy with error handling
try:
    import numpy as np
except ImportError:
    print("Warning: NumPy not installed. Some features will be limited.")
    print("Install with: pip install numpy")
    np = None


def example_enumerate_sessions():
    """Example: Enumerate all audio sessions"""
    print("=" * 60)
    print("EXAMPLE 1: Enumerate Audio Sessions")
    print("=" * 60)
    
    try:
        # Create session enumerator
        enumerator = pypac.SessionEnumerator()
        
        # Get all sessions
        sessions = enumerator.enumerate_sessions()
    except Exception as e:
        print(f"Error creating SessionEnumerator: {e}")
        print("Make sure you have proper permissions.")
        return
    
    print(f"\nFound {len(sessions)} audio sessions:\n")
    
    for session in sessions:
        state_names = {0: "Inactive", 1: "Active", 2: "Expired"}
        state = state_names.get(session.state, "Unknown")
        
        print(f"Process: {session.process_name} (PID: {session.process_id})")
        print(f"  State: {state}")
        print(f"  Volume: {session.volume:.2%}")
        print(f"  Muted: {'Yes' if session.muted else 'No'}")
        print()


def example_simple_capture():
    """Example: Simple system-wide audio capture"""
    print("=" * 60)
    print("EXAMPLE 2: Simple Audio Capture")
    print("=" * 60)
    
    if np is None:
        print("Skipping audio capture example (NumPy not installed)")
        return
    
    try:
        # Create loopback capture
        loopback = pypac.SimpleLoopback()
    except Exception as e:
        print(f"Error creating SimpleLoopback: {e}")
        return
    
    print("\nStarting audio capture...")
    if loopback.start():
        print("Capture started! Recording for 3 seconds...")
        print("Please play some audio...\n")
        
        total_samples = 0
        for i in range(3):
            time.sleep(1)
            
            # Get captured audio
            audio_buffer = loopback.get_buffer()
            samples = len(audio_buffer)
            total_samples += samples
            
            if samples > 0:
                # Calculate RMS (Root Mean Square) for volume indication
                rms = np.sqrt(np.mean(audio_buffer**2))
                db = 20 * np.log10(rms + 1e-10)
                
                # Create simple VU meter
                meter_width = 30
                normalized = min(1.0, max(0.0, (db + 60) / 60))  # Normalize -60dB to 0dB
                filled = int(normalized * meter_width)
                meter = "█" * filled + "░" * (meter_width - filled)
                
                print(f"  [{i+1}s] {meter} {samples:6d} samples | {db:+6.1f} dB")
            else:
                print(f"  [{i+1}s] {'░' * 30} No audio")
        
        loopback.stop()
        print(f"\nCapture stopped. Total samples: {total_samples:,}")
    else:
        print("Failed to start capture!")


def example_volume_control():
    """Example: Control volume of specific process"""
    print("=" * 60)
    print("EXAMPLE 3: Volume Control")
    print("=" * 60)
    
    try:
        enumerator = pypac.SessionEnumerator()
        sessions = enumerator.enumerate_sessions()
    except Exception as e:
        print(f"Error: {e}")
        return
    
    # Find active sessions
    active_sessions = [s for s in sessions if s.state == 1]
    
    if not active_sessions:
        print("\nNo active audio sessions found.")
        print("Please play some audio and try again.")
        return
    
    # Use first active session as example
    target = active_sessions[0]
    
    print(f"\nTarget process: {target.process_name} (PID: {target.process_id})")
    print(f"Current volume: {target.volume:.2%}")
    
    # Set volume to 50%
    new_volume = 0.5
    print(f"Setting volume to {new_volume:.2%}...")
    
    if enumerator.set_session_volume(target.process_id, new_volume):
        print("Volume changed successfully!")
        
        # Verify the change
        sessions = enumerator.enumerate_sessions()
        for s in sessions:
            if s.process_id == target.process_id:
                print(f"Verified new volume: {s.volume:.2%}")
                break
    else:
        print("Failed to change volume.")


def main():
    print("WINDOWS AUDIO CAPTURE LIBRARY - EXAMPLES")
    print("=" * 60)
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
    # example_volume_control()  # Uncomment to test volume control
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()