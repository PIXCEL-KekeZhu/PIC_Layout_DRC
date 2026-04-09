#!/usr/bin/env python3
"""
Open a GDS file in KLayout.
Usage:
    uv run klayout_opengds.py <gds_file>
    ./klayout_opengds.py <gds_file>
"""
import os
import sys
from klayout_utils import load_env, klayout_open

load_env()

gds_file = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'layout_gds/py_klayout_example.gds')
print(f"Opening {gds_file} in KLayout...")
klayout_open("-e", gds_file)
