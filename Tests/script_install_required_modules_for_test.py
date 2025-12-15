import subprocess
import sys
import importlib
import os

def install_module(module_name):
    """Install a Python module using pip."""
    
    pip = ""
    if os.name == 'nt':
        pip = "pip"
    else:
        pip = "pip3"
        
    try:
        subprocess.check_call([sys.executable, "-m", pip, "install", module_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install module {module_name}: {e}")
        
    return False
        
def check_module_installed(module_name):
    """Check if a Python module is installed."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False
    
if __name__ == "__main__":
    required_modules = [
        "starlette",
        "fastapi",
        "aiohttp",
        "flask",
        "django",
    ]
    
    for module in required_modules:
        if not check_module_installed(module):
            print(f"[INFO] Module {module} is not installed. Attempting to install...")
            
            if install_module(module):
                print(f"[INFO] Rechecking installation of module: {module}")
            else:
                print(f"[ERROR] Installation attempt for module {module} failed.")
                continue
            
        if not check_module_installed(module):
            print(f"[ERROR] Module {module} could not be installed. Please install it manually.")
            
        print(f"[INFO] Module {module} is installed.")
            
    print("[INFO] All required modules are installed.")
