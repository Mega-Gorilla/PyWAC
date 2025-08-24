"""
Debug script to investigate process name detection issues
"""

import sys
import os
import ctypes
from ctypes import wintypes
import psutil  # Will need: pip install psutil

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dist'))

def get_process_info_with_psutil(pid):
    """Get process information using psutil for comparison"""
    try:
        process = psutil.Process(pid)
        return {
            'name': process.name(),
            'exe': process.exe(),
            'cmdline': process.cmdline(),
            'status': process.status()
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        return {'error': str(e)}

def main():
    try:
        import pypac
    except ImportError as e:
        print(f"[ERROR] Failed to import pypac: {e}")
        return
    
    print("=" * 60)
    print("PROCESS NAME DETECTION DEBUG")
    print("=" * 60)
    
    # Get sessions from pypac
    enumerator = pypac.SessionEnumerator()
    sessions = enumerator.enumerate_sessions()
    
    print(f"\n[INFO] Found {len(sessions)} audio sessions\n")
    
    # Check if psutil is available
    has_psutil = False
    try:
        import psutil
        has_psutil = True
        print("[OK] psutil available for cross-checking\n")
    except ImportError:
        print("[WARN] psutil not installed - install with: pip install psutil\n")
    
    # Analyze each session
    for i, session in enumerate(sessions, 1):
        print(f"Session {i}:")
        print(f"  PID: {session.process_id}")
        print(f"  PyPAC Name: {session.process_name}")
        print(f"  Display Name: {session.display_name if session.display_name else '(empty)'}")
        print(f"  State: {['Inactive', 'Active', 'Expired'][session.state]}")
        
        # If pypac returns "Unknown", try to get more info
        if session.process_name == "Unknown" and has_psutil:
            psutil_info = get_process_info_with_psutil(session.process_id)
            if 'error' not in psutil_info:
                print(f"  Actual Name (psutil): {psutil_info['name']}")
                print(f"  Executable: {psutil_info['exe']}")
            else:
                print(f"  psutil Error: {psutil_info['error']}")
        
        print()
    
    # Analysis summary
    unknown_count = sum(1 for s in sessions if s.process_name == "Unknown")
    if unknown_count > 0:
        print(f"\n[ANALYSIS] {unknown_count} of {len(sessions)} sessions have 'Unknown' process names")
        print("\nPossible causes:")
        print("1. Insufficient permissions to access process information")
        print("2. Process is running with higher privileges")
        print("3. Process is a protected/system process")
        print("4. GetModuleBaseNameA API limitation")
        print("\nSuggested fix: Use QueryFullProcessImageNameA instead of GetModuleBaseNameA")

if __name__ == "__main__":
    main()