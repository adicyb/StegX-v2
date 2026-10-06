import sys
import subprocess
from pathlib import Path

def main():
    args = sys.argv[1:]
    
    try:
        from importlib.resources import files
        app_path = str(files("stegx.ui") / "app.py")
    except ImportError:
        import stegx.ui
        app_path = str(Path(stegx.ui.__file__).parent / "app.py")
    
    if not Path(app_path).is_file():
        print(f"Error: Could not locate StegX Web Console app at {app_path}", file=sys.stderr)
        sys.exit(1)
        
    cmd = [sys.executable, "-m", "streamlit", "run", app_path] + args
    
    try:
        import os
        if hasattr(os, "execv"):
            os.execv(sys.executable, cmd)
        else:
            sys.exit(subprocess.call(cmd))
    except Exception as e:
        print(f"Error launching Web Console: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
