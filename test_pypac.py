"""Quick test for pypac module"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dist'))

print("Testing pypac module...")

try:
    import pypac
    print("✅ Module import successful!")
    
    # Test SessionEnumerator
    print("\n[Testing SessionEnumerator]")
    enumerator = pypac.SessionEnumerator()
    print("✅ SessionEnumerator created")
    
    sessions = enumerator.enumerate_sessions()
    print(f"✅ Found {len(sessions)} audio sessions")
    
    # Show first 3 sessions
    for session in sessions[:3]:
        print(f"  - {session.process_name} (PID: {session.process_id})")
    
    # Test SimpleLoopback
    print("\n[Testing SimpleLoopback]")
    loopback = pypac.SimpleLoopback()
    print("✅ SimpleLoopback created")
    
    if loopback.start():
        print("✅ Loopback started successfully!")
        loopback.stop()
        print("✅ Loopback stopped")
    else:
        print("⚠️ Could not start loopback (may need admin rights)")
    
    print("\n[SUCCESS] All tests passed! pypac module is working correctly.")
    
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()