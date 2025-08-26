"""
PyWAC Module Health Check and Diagnostics
"""

import sys
import os
import platform
import ctypes

def check_environment():
    """Check system environment"""
    print("=" * 60)
    print("SYSTEM ENVIRONMENT CHECK")
    print("=" * 60)
    
    # Python info
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    
    # Check if 64-bit Python
    is_64bit = sys.maxsize > 2**32
    print(f"Python Architecture: {'64-bit' if is_64bit else '32-bit'}")
    
    if not is_64bit:
        print("WARNING: 32-bit Python detected. PyWAC requires 64-bit Python.")
        return False
    
    # Check Windows version
    if not sys.platform.startswith('win'):
        print("ERROR: PyWAC only works on Windows.")
        return False
    
    # Check admin privileges
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        print(f"Administrator Privileges: {'Yes' if is_admin else 'No'}")
    except:
        print("Administrator Privileges: Unknown")
    
    return True

def check_dependencies():
    """Check required dependencies"""
    print("\n" + "=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    
    dependencies = {
        'pybind11': 'Build requirement',
        'numpy': 'Audio processing',
    }
    
    for module, purpose in dependencies.items():
        try:
            __import__(module)
            print(f"[OK] {module} - {purpose}")
        except ImportError:
            print(f"[MISSING] {module} - {purpose}")
            print(f"  Install with: pip install {module}")

def check_module_files():
    """Check if module files exist"""
    print("\n" + "=" * 60)
    print("MODULE FILES CHECK")
    print("=" * 60)
    
    # Check in parent directory where modules are built
    parent_path = os.path.dirname(os.path.dirname(__file__))
    
    modules_found = []
    modules_missing = []
    
    # Expected modules for v0.4.1
    expected_modules = {
        'process_loopback_queue': 'Process audio capture (v0.4.1)',
        '_pywac_native': 'Session management'
    }
    
    # Look for .pyd files
    import glob
    pyd_files = glob.glob(os.path.join(parent_path, '*.pyd'))
    # Also check pywac subdirectory
    pyd_files.extend(glob.glob(os.path.join(parent_path, 'pywac', '*.pyd')))
    
    for module_name, description in expected_modules.items():
        found = False
        for pyd in pyd_files:
            basename = os.path.basename(pyd)
            if module_name in basename:
                size = os.path.getsize(pyd)
                print(f"[OK] {basename} ({size:,} bytes) - {description}")
                modules_found.append(module_name)
                found = True
                break
        
        if not found:
            print(f"[MISSING] {module_name} - {description}")
            modules_missing.append(module_name)
    
    if modules_missing:
        print("\nTo build missing modules:")
        print("  python setup.py build_ext --inplace")
        return False
    
    return True

def check_vcredist():
    """Check for Visual C++ Redistributable"""
    print("\n" + "=" * 60)
    print("VISUAL C++ REDISTRIBUTABLE CHECK")
    print("=" * 60)
    
    # Common MSVC runtime DLLs
    dlls = [
        'msvcp140.dll',
        'vcruntime140.dll',
        'vcruntime140_1.dll'
    ]
    
    system32 = os.path.join(os.environ['SystemRoot'], 'System32')
    
    all_found = True
    for dll in dlls:
        dll_path = os.path.join(system32, dll)
        if os.path.exists(dll_path):
            print(f"[OK] {dll}")
        else:
            print(f"[MISSING] {dll}")
            all_found = False
    
    if not all_found:
        print("\nVisual C++ Redistributable may not be installed.")
        print("Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    
    return all_found

def test_import():
    """Try to import pywac module"""
    print("\n" + "=" * 60)
    print("MODULE IMPORT TEST")
    print("=" * 60)
    
    # Add parent directory to path
    parent_path = os.path.dirname(os.path.dirname(__file__))
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
    
    try:
        import pywac
        print("[SUCCESS] pywac module imported!")
        
        # Check available classes
        classes = ['SessionEnumerator', 'SimpleLoopback']
        for cls in classes:
            if hasattr(pywac, cls):
                print(f"  [OK] pywac.{cls} available")
            else:
                print(f"  [MISSING] pywac.{cls} not found")
        
        return True
        
    except ImportError as e:
        print(f"[FAILED] Import error: {e}")
        
        if "DLL load failed" in str(e):
            print("\nDLL load failed. Possible causes:")
            print("1. Missing Visual C++ Redistributable")
            print("2. Architecture mismatch (32-bit vs 64-bit)")
            print("3. Corrupted .pyd file")
            
            # Try to get more specific error
            if hasattr(e, '__cause__'):
                print(f"Underlying error: {e.__cause__}")
        
        return False
    except Exception as e:
        print(f"[FAILED] Unexpected error: {e}")
        return False

def test_functionality():
    """Test basic functionality"""
    print("\n" + "=" * 60)
    print("FUNCTIONALITY TEST")
    print("=" * 60)
    
    try:
        import pywac
        
        # Test SessionEnumerator
        print("\nTesting SessionEnumerator...")
        try:
            enumerator = pywac.SessionEnumerator()
            sessions = enumerator.enumerate_sessions()
            print(f"  [OK] Found {len(sessions)} audio sessions")
        except Exception as e:
            print(f"  [FAILED] {e}")
        
        # Test SimpleLoopback
        print("\nTesting SimpleLoopback...")
        try:
            loopback = pywac.SimpleLoopback()
            print("  [OK] SimpleLoopback created")
        except Exception as e:
            print(f"  [FAILED] {e}")
        
    except ImportError:
        print("Cannot test functionality - module not imported")

def main():
    print("PyWAC MODULE HEALTH CHECK")
    print("=" * 60)
    print()
    
    # Run all checks
    env_ok = check_environment()
    check_dependencies()
    files_ok = check_module_files()
    vcredist_ok = check_vcredist()
    
    if env_ok and files_ok:
        import_ok = test_import()
        if import_ok:
            test_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if env_ok and files_ok and import_ok:
        print("[SUCCESS] PyWAC is ready to use!")
    else:
        print("[FAILED] PyWAC has issues that need to be resolved.")
        print("\nNext steps:")
        print("1. Fix any missing dependencies")
        print("2. Install Visual C++ Redistributable if missing")
        print("3. Rebuild with: python setup.py build_ext --inplace")

if __name__ == "__main__":
    main()