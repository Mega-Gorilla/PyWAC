"""Quick test for PyWAC v0.4.1 modules"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing PyWAC v0.4.1 modules...")
print("=" * 60)

def test_session_module():
    """Test session management module"""
    print("\n[Testing Session Management Module]")
    try:
        import pywac
        print("[OK] pywac module imported")
        
        # Test session listing
        sessions = pywac.list_audio_sessions()
        print(f"[OK] Found {len(sessions)} audio sessions")
        
        # Show first 3 sessions
        for session in sessions[:3]:
            # Handle both dict and object formats
            if isinstance(session, dict):
                name = session.get('name', session.get('process_name', 'Unknown'))
                pid = session.get('pid', session.get('process_id', 0))
            else:
                name = getattr(session, 'name', getattr(session, 'process_name', 'Unknown'))
                pid = getattr(session, 'pid', getattr(session, 'process_id', 0))
            print(f"  - {name} (PID: {pid})")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_queue_module():
    """Test process audio capture module"""
    print("\n[Testing Process Audio Capture Module]")
    try:
        import process_loopback_queue as queue_module
        print("[OK] process_loopback_queue module imported")
        
        # List processes
        processes = queue_module.list_audio_processes()
        print(f"[OK] Listed {len(processes)} processes")
        
        # Check if event-driven mode would be available
        capture = queue_module.QueueBasedProcessCapture()
        print("[OK] QueueBasedProcessCapture created")
        
        # Note: Don't actually start capture in test
        print("  (Not starting actual capture in test)")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("  Make sure to build the module: python setup.py build_ext --inplace")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_streaming():
    """Test streaming interface"""
    print("\n[Testing Streaming Interface]")
    try:
        from pywac.queue_streaming import QueueBasedStreamingCapture
        print("[OK] QueueBasedStreamingCapture imported")
        
        # Just test import and creation
        # Don't actually capture
        print("  Streaming interface available")
        
        return True
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def main():
    """Run all tests"""
    results = []
    
    # Test each component
    results.append(("Session Management", test_session_module()))
    results.append(("Queue Module", test_queue_module()))
    results.append(("Streaming Interface", test_streaming()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[OK] PASS" if passed else "[ERROR] FAIL"
        print(f"{name:.<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] All tests passed! PyWAC v0.4.1 is working correctly.")
    else:
        print("[FAILED] Some tests failed. Check the output above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())