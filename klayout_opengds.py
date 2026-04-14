#!/usr/bin/env python3
"""
Open a GDS file in KLayout.
Usage:
    uv run klayout_opengds.py <gds_file>
    ./klayout_opengds.py <gds_file>
"""
import os
import sys
from klayout_utils import load_env, klayout_open, find_latest_gds

load_env()

if len(sys.argv) > 1:
    gds_file = os.path.abspath(sys.argv[1])
else:
    gds_file = find_latest_gds()

print(f"Opening {gds_file} in KLayout...")
klayout_open("-e", gds_file)
