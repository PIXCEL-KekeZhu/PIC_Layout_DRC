"""
Shared KLayout utilities: env loading, binary detection, process check, launch.
"""
import os
import platform
import subprocess

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

def get_klayout_bin() -> str:
    exe = os.environ.get('KLAYOUT_EXE')
    if exe:
        return exe
    if platform.system() == 'Darwin':
        return '/Applications/klayout.app/Contents/MacOS/klayout'
    # Try to find klayout_app.exe in common Windows install paths
    candidates = [
        os.path.expandvars(r'%APPDATA%\KLayout\klayout_app.exe'),
        r'C:\Program Files\KLayout\klayout_app.exe',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return 'klayout'

def is_klayout_running() -> bool:
    system = platform.system()
    try:
        if system == 'Windows':
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq klayout_app.exe', '/NH'],
                capture_output=True, text=True
            )
            return 'klayout_app.exe' in result.stdout
        else:
            result = subprocess.run(['pgrep', '-x', 'klayout'], capture_output=True)
            return result.returncode == 0
    except Exception:
        return False

def klayout_open(*args: str):
    """
    Open files in KLayout.
    - If KLayout is already running, uses -s to load into the same view.
    - Otherwise launches a new instance.
    """
    klayout_bin = get_klayout_bin()
    running = is_klayout_running()

    # Always ensure editor mode is enabled
    args = list(args)
    if "-e" not in args:
        args = ["-e"] + args

    if running:
        print("KLayout (Editor) is already open — opening in a new panel.")
        cmd = [klayout_bin] + args
    else:
        print("Launching KLayout (Editor).")
        cmd = [klayout_bin] + args

    subprocess.Popen(cmd)
