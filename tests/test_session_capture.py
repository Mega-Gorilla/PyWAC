"""Test Windows Audio Session enumeration and capture"""

import pypac
import numpy as np
import time

def test_session_enumeration():
    """Test audio session enumeration"""
    print("=" * 60)
    print("AUDIO SESSION ENUMERATION TEST")
    print("=" * 60)
    
    try:
        # Create session enumerator
        enumerator = pypac.SessionEnumerator()
        print("[OK] SessionEnumerator created")
        
        # Enumerate sessions
        sessions = enumerator.enumerate_sessions()
        print(f"\n[Found {len(sessions)} audio sessions]")
        
        # Display session information
        for session in sessions:
            state_names = {0: "Inactive", 1: "Active", 2: "Expired"}
            state = state_names.get(session.state, "Unknown")
            
            print(f"\nProcess: {session.process_name} (PID: {session.process_id})")
            print(f"  State: {state}")
            print(f"  Volume: {session.volume:.2f}")
            print(f"  Muted: {session.muted}")
            if session.display_name:
                print(f"  Display Name: {session.display_name}")
        
        # Find active audio sessions
        active_sessions = [s for s in sessions if s.state == 1]  # Active
        if active_sessions:
            print(f"\n[{len(active_sessions)} ACTIVE sessions]")
            for session in active_sessions:
                print(f"  - {session.process_name} (PID: {session.process_id})")
        
    except Exception as e:
        print(f"[ERROR] Session enumeration failed: {e}")
        import traceback
        traceback.print_exc()

def test_simple_loopback():
    """Test simple WASAPI loopback capture"""
    print("\n" + "=" * 60)
    print("SIMPLE LOOPBACK CAPTURE TEST")
    print("=" * 60)
    
    try:
        # Create simple loopback
        loopback = pypac.SimpleLoopback()
        print("[OK] SimpleLoopback created")
        
        # Start capture
        if loopback.start():
            print("[OK] Loopback capture started")
            print("Please play some audio...")
            
            # Capture for 3 seconds
            total_samples = 0
            for i in range(3):
                time.sleep(1)
                
                # Get audio buffer
                buffer = loopback.get_buffer()
                samples = len(buffer)
                total_samples += samples
                
                if samples > 0:
                    # Calculate RMS
                    rms = np.sqrt(np.mean(buffer**2))
                    db = 20 * np.log10(rms + 1e-10)
                    print(f"  Second {i+1}: {samples:6d} samples | RMS: {rms:.4f} | {db:+6.1f} dB")
                else:
                    print(f"  Second {i+1}: No audio captured")
            
            # Stop capture
            loopback.stop()
            print("[OK] Loopback stopped")
            print(f"\nTotal samples captured: {total_samples}")
            
            if total_samples > 0:
                print("SUCCESS: Audio captured successfully!")
            else:
                print("WARNING: No audio captured (is audio playing?)")
        else:
            print("[FAILED] Could not start loopback capture")
            
    except Exception as e:
        print(f"[ERROR] Loopback capture failed: {e}")
        import traceback
        traceback.print_exc()

def test_volume_control():
    """Test session volume control"""
    print("\n" + "=" * 60)
    print("SESSION VOLUME CONTROL TEST")
    print("=" * 60)
    
    try:
        enumerator = pypac.SessionEnumerator()
        sessions = enumerator.enumerate_sessions()
        
        # Find an active session
        active_sessions = [s for s in sessions if s.state == 1]
        if active_sessions:
            target = active_sessions[0]
            print(f"Testing volume control for: {target.process_name} (PID: {target.process_id})")
            print(f"  Current volume: {target.volume:.2f}")
            
            # Try to set volume to 50%
            new_volume = 0.5
            if enumerator.set_session_volume(target.process_id, new_volume):
                print(f"  [OK] Volume set to {new_volume:.2f}")
                
                # Verify change
                sessions = enumerator.enumerate_sessions()
                for s in sessions:
                    if s.process_id == target.process_id:
                        print(f"  Verified volume: {s.volume:.2f}")
                        break
            else:
                print("  [FAILED] Could not set volume")
        else:
            print("No active sessions found for volume control test")
            
    except Exception as e:
        print(f"[ERROR] Volume control test failed: {e}")

def main():
    print("WINDOWS AUDIO SESSION CAPTURE TEST")
    print("=" * 60)
    print()
    
    # Check admin status
    import ctypes
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Running as Administrator: {'Yes' if is_admin else 'No'}")
    except:
        pass
    
    print()
    
    # Run tests
    test_session_enumeration()
    test_simple_loopback()
    # test_volume_control()  # Uncomment to test volume control
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()