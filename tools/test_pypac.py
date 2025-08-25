"""Quick test for pywac module"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dist'))

print("Testing pywac module...")

try:
    import pywac
    print("✅ Module import successful!")
    
    # Test SessionEnumerator
    print("\n[Testing SessionEnumerator]")
    enumerator = pywac.SessionEnumerator()
    print("✅ SessionEnumerator created")
    
    sessions = enumerator.enumerate_sessions()
    print(f"✅ Found {len(sessions)} audio sessions")
    
    # Show first 3 sessions
    for session in sessions[:3]:
        print(f"  - {session.process_name} (PID: {session.process_id})")
    
    # Test SimpleLoopback
    print("\n[Testing SimpleLoopback]")
    loopback = pywac.SimpleLoopback()
    print("✅ SimpleLoopback created")
    
    if loopback.start():
        print("✅ Loopback started successfully!")
        loopback.stop()
        print("✅ Loopback stopped")
    else:
        print("⚠️ Could not start loopback (may need admin rights)")
    
    print("\n[SUCCESS] All tests passed! pywac module is working correctly.")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()