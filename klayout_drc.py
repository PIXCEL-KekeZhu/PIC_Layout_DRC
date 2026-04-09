#!/usr/bin/env python3
"""
Run KLayout DRC on a GDS file using drc_rules/pic_drc.drc.
Usage: uv run drc.py [gds_file]
Output reports are saved to drc_outputs/
"""
import subprocess
import sys
import os

# Load .env if present
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DRC_SCRIPT  = os.path.join(BASE_DIR, 'drc_rules', 'pic_drc.drc')
OUTPUT_DIR  = os.path.join(BASE_DIR, 'drc_outputs')

def get_klayout_bin() -> str:
    exe = os.environ.get('KLAYOUT_EXE')
    if exe:
        return exe
    import platform
    if platform.system() == 'Darwin':
        return '/Applications/klayout.app/Contents/MacOS/klayout'
    return 'klayout'

def run_drc(gds_file: str):
    gds_file   = os.path.abspath(gds_file)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_name  = os.path.splitext(os.path.basename(gds_file))[0]
    report_file = os.path.join(OUTPUT_DIR, f"{base_name}_drc.lyrdb")
    klayout_bin = get_klayout_bin()

    n_threads = os.cpu_count() or 1

    print(f"Running DRC on:  {gds_file}")
    print(f"DRC rules:       {DRC_SCRIPT}")
    print(f"Report output:   {report_file}")
    print(f"Threads:         {n_threads}")

    subprocess.run(
        [
            klayout_bin, "-b", "-r", DRC_SCRIPT,
            "-rd", f"input={gds_file}",
            "-rd", f"output={report_file}",
            "-rd", f"threads={n_threads}",
        ],
        check=True
    )
    print("DRC complete.")

    # Open GDS + report in KLayout
    subprocess.Popen([klayout_bin, "-e", gds_file, "-m", report_file])
    print("Opening results in KLayout...")

if __name__ == "__main__":
    gds = sys.argv[1] if len(sys.argv) > 1 else "layout_gds/example.gds"
    run_drc(gds)
