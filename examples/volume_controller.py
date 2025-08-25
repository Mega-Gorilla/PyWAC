"""
PyWAC Volume Controller - Interactive volume control for running applications
Uses the high-level pywac package API for easy audio session management
"""

import pywac
import sys

def main():
    print("=" * 60)
    print("PYWAC VOLUME CONTROLLER")
    print("=" * 60)
    print(f"Version: {pywac.__version__}")
    print()
    
    # Get active sessions
    active_sessions = pywac.get_active_sessions()
    
    if not active_sessions:
        print("No active audio sessions found.")
        print("Please play audio in an application and try again.")
        return
    
    # Get detailed session info for active apps
    sessions = pywac.list_audio_sessions(active_only=True)
    
    # Display sessions
    print("Active Audio Sessions:")
    for i, session in enumerate(sessions, 1):
        mute_status = "[MUTED]" if session['is_muted'] else f"[VOL: {session['volume_percent']:.0f}%]"
        print(f"{i}. {session['process_name']} - {mute_status}")
    
    # User selection
    print("\nSelect an application to control (number):")
    try:
        choice = int(input("> ")) - 1
        if 0 <= choice < len(sessions):
            selected = sessions[choice]
            app_name = selected['process_name']
            
            print(f"\nControlling: {app_name}")
            print("Commands:")
            print("  0-100  : Set volume to specific percentage")
            print("  +/-N   : Adjust volume by N percent (e.g., +10 or -20)")
            print("  m      : Toggle mute")
            print("  q      : Quit")
            
            while True:
                current_vol = pywac.get_app_volume(app_name)
                if current_vol is not None:
                    print(f"\nCurrent volume: {current_vol * 100:.0f}%")
                
                action = input("> ").strip().lower()
                
                if action == 'q':
                    break
                elif action == 'm':
                    # Toggle mute using SessionManager for mute control
                    manager = pywac.SessionManager()
                    session = manager.find_session(app_name)
                    if session:
                        new_mute = not session.is_muted
                        if manager.set_mute(app_name, new_mute):
                            print(f"[OK] {'Muted' if new_mute else 'Unmuted'} {app_name}")
                        else:
                            print("[ERROR] Failed to change mute state")
                elif action.startswith('+') or action.startswith('-'):
                    # Adjust volume
                    try:
                        delta = float(action) / 100  # Convert percentage to fraction
                        new_volume = pywac.adjust_volume(app_name, delta)
                        if new_volume is not None:
                            print(f"[OK] Adjusted {app_name} volume to {new_volume * 100:.0f}%")
                        else:
                            print("[ERROR] Failed to adjust volume")
                    except ValueError:
                        print("[ERROR] Invalid adjustment value")
                else:
                    # Set absolute volume
                    try:
                        volume = float(action)
                        if 0 <= volume <= 100:
                            if pywac.set_app_volume(app_name, volume / 100):
                                print(f"[OK] Set {app_name} volume to {volume:.0f}%")
                            else:
                                print("[ERROR] Failed to change volume")
                        else:
                            print("[ERROR] Volume must be between 0 and 100")
                    except ValueError:
                        print("[ERROR] Invalid input. Enter a number 0-100, +/-N, 'm', or 'q'")
        else:
            print("[ERROR] Invalid selection")
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\n[INFO] Exiting...")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Failed to import pywac module")
        print("=" * 60)
        print(f"Details: {e}")
        print("\nPlease install the package:")
        print("  pip install -e .")
        print("\nOr build the module:")
        print("  python setup.py build_ext --inplace")
        sys.exit(1)