#!/usr/bin/env python3
"""
Open a GDS file in KLayout.
Usage:
    uv run klayout_opengds.py <gds_file>
    ./klayout_opengds.py <gds_file>
"""
import os
import sys
import glob
from klayout_utils import load_env, klayout_open

load_env()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if len(sys.argv) > 1:
    gds_file = os.path.abspath(sys.argv[1])
else:
    gds_files = glob.glob(os.path.join(BASE_DIR, 'layout_gds', '*.gds'))
    if not gds_files:
        print("No GDS files found in layout_gds/")
        sys.exit(1)
    gds_file = max(gds_files, key=os.path.getmtime)
    print(f"Latest GDS: {os.path.basename(gds_file)}")

print(f"Opening {gds_file} in KLayout...")
klayout_open("-e", gds_file)
