"""
PyPAC Quick Test - Simple functionality check
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dist'))

try:
    import pypac
    print("✅ PyPAC module loaded successfully!")
    
    # Quick test
    enumerator = pypac.SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    
    print(f"\n📊 Found {len(sessions)} audio sessions:")
    for session in sessions[:5]:  # Show first 5
        status = "🔊" if session.state == 1 else "🔇"
        print(f"  {status} {session.process_name} (PID: {session.process_id})")
    
    if len(sessions) > 5:
        print(f"  ... and {len(sessions) - 5} more")
    
except ImportError as e:
    print(f"❌ Failed to import PyPAC: {e}")
    print("\nPlease build the module first:")
    print("  python setup.py build_ext --inplace")
except Exception as e:
    print(f"❌ Error: {e}")