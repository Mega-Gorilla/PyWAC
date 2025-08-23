"""Simple test for audio session module"""

def main():
    print("Testing audio_session_capture module...")
    
    try:
        import audio_session_capture as asc
        print("[OK] Module imported")
        
        # Test SimpleLoopback
        print("\n[Testing SimpleLoopback]")
        loopback = asc.SimpleLoopback()
        print("[OK] SimpleLoopback instance created")
        
        success = loopback.start()
        if success:
            print("[OK] Loopback started")
            
            import time
            time.sleep(1)
            
            buffer = loopback.get_buffer()
            print(f"[OK] Got buffer with {len(buffer)} samples")
            
            loopback.stop()
            print("[OK] Loopback stopped")
        else:
            print("[FAILED] Could not start loopback")
        
        # Test SessionEnumerator
        print("\n[Testing SessionEnumerator]")
        enumerator = asc.SessionEnumerator()
        print("[OK] SessionEnumerator instance created")
        
        sessions = enumerator.enumerate_sessions()
        print(f"[OK] Found {len(sessions)} sessions")
        
        for session in sessions[:3]:  # Show first 3
            print(f"  - {session.process_name} (PID: {session.process_id})")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()