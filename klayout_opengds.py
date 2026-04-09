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

gds_file = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'nazca_export.gds')

proc = subprocess.Popen(['open', '-a', 'KLayout', gds_file])
print(f"Opening {gds_file} in KLayout...")
proc.wait()
