"""
PyPAC Quick Test - Simple functionality check using package API
"""

import pypac

try:
    print("[OK] PyPAC module loaded successfully!")
    print(f"     Version: {pypac.__version__}")
    
    # Use the high-level API to list sessions
    sessions = pypac.list_audio_sessions()
    
    print(f"\n[INFO] Found {len(sessions)} audio sessions:")
    for session in sessions[:5]:  # Show first 5
        status = "[ACTIVE]" if session['is_active'] else "[INACTIVE]"
        print(f"  {status} {session['process_name']} (PID: {session['process_id']})")
    
    if len(sessions) > 5:
        print(f"  ... and {len(sessions) - 5} more")
    
    # Test finding active sessions
    active_sessions = pypac.get_active_sessions()
    if active_sessions:
        print(f"\n[INFO] Active sessions: {', '.join(active_sessions)}")
    else:
        print("\n[INFO] No applications currently playing audio")
    
except ImportError as e:
    print(f"[ERROR] Failed to import PyPAC: {e}")
    print("\nPlease install the package:")
    print("  pip install -e .")
except Exception as e:
    print(f"[ERROR] Error: {e}")