#!/usr/bin/env python3
"""
Open a GDS file in KLayout.
Usage:
    uv run klayout_opengds.py <gds_file>
    ./klayout_opengds.py <gds_file>
"""
import subprocess
import os
import sys
import platform

# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

gds_file = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'layout_gds/py_klayout_example.gds')

system = platform.system()
if system == 'Darwin':
    proc = subprocess.Popen(['open', '-a', 'KLayout', gds_file])
elif system == 'Windows':
    klayout_exe = os.environ.get('KLAYOUT_EXE')
    if not klayout_exe:
        raise EnvironmentError("KLAYOUT_EXE is not set. Add it to your .env file or environment variables.")
    proc = subprocess.Popen([klayout_exe, gds_file])
else:
    proc = subprocess.Popen(['klayout', gds_file])

print(f"Opening {gds_file} in KLayout...")
proc.wait()
