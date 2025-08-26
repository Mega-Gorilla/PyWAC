"""
Debug script to investigate process name detection issues
"""

import sys
import os
import ctypes
from ctypes import wintypes
import psutil  # Will need: pip install psutil

# Add parent directory to path
parent_path = os.path.dirname(os.path.dirname(__file__))
if parent_path not in sys.path:
    sys.path.insert(0, parent_path)

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
        import pywac
    except ImportError as e:
        print(f"[ERROR] Failed to import pywac: {e}")
        return
    
    print("=" * 60)
    print("PROCESS NAME DETECTION DEBUG")
    print("=" * 60)
    
    # Try to get sessions from pywac
    try:
        if hasattr(pywac, 'SessionEnumerator'):
            enumerator = pywac.SessionEnumerator()
            sessions = enumerator.enumerate_sessions()
        elif hasattr(pywac, 'list_audio_sessions'):
            sessions = pywac.list_audio_sessions()
        else:
            print("[ERROR] pywac module doesn't have expected methods")
            print(f"Available attributes: {dir(pywac)}")
            return
    except Exception as e:
        print(f"[ERROR] Failed to enumerate sessions: {e}")
        return
    
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
        # Handle both dict and object formats
        if isinstance(session, dict):
            pid = session.get('pid', session.get('process_id', 0))
            name = session.get('name', session.get('process_name', 'Unknown'))
            display_name = session.get('display_name', '(empty)')
            state = session.get('state', -1)
        else:
            pid = getattr(session, 'process_id', getattr(session, 'pid', 0))
            name = getattr(session, 'process_name', getattr(session, 'name', 'Unknown'))
            display_name = getattr(session, 'display_name', '(empty)')
            state = getattr(session, 'state', -1)
        
        print(f"Session {i}:")
        print(f"  PID: {pid}")
        print(f"  PyWAC Name: {name}")
        print(f"  Display Name: {display_name if display_name else '(empty)'}")
        try:
            state_int = int(state) if state != -1 else -1
            if state_int >= 0 and state_int <= 2:
                print(f"  State: {['Inactive', 'Active', 'Expired'][state_int]}")
        except (ValueError, TypeError):
            pass  # Skip state if it's not a valid number
        
        # If pywac returns "Unknown", try to get more info
        if name == "Unknown" and has_psutil:
            psutil_info = get_process_info_with_psutil(pid)
            if 'error' not in psutil_info:
                print(f"  Actual Name (psutil): {psutil_info['name']}")
                print(f"  Executable: {psutil_info['exe']}")
            else:
                print(f"  psutil Error: {psutil_info['error']}")
        
        print()
    
    # Analysis summary
    unknown_count = sum(1 for s in sessions if (s.get('name', s.get('process_name', 'Unknown')) if isinstance(s, dict) else getattr(s, 'process_name', getattr(s, 'name', 'Unknown'))) == "Unknown")
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