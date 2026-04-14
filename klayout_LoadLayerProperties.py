#!/usr/bin/env python3
"""
klayout_LoadLayerProperties.py — Open a GDS file in KLayout with a .lyp file

Opens the given GDS (or the most recently modified one in layout_gds/) in
KLayout with the specified layer properties file applied.

Usage:
  python klayout_LoadLayerProperties.py [gds_file] [--lyp <file.lyp>]

Defaults:
  gds_file   most recently modified file in layout_gds/
  --lyp      layout_lyp/pic_process.lyp
"""

import argparse
import os
import sys
from klayout_utils import load_env, klayout_open, find_latest_gds

load_env()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LYP = os.path.join(BASE_DIR, "layout_lyp", "pic_process.lyp")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Open a GDS file in KLayout with layer properties applied.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "gds",
        nargs="?",
        default=None,
        help="Path to GDS file (default: most recently modified in layout_gds/)",
    )
    parser.add_argument(
        "--lyp",
        default=DEFAULT_LYP,
        metavar="FILE",
        help="Path to .lyp layer properties file",
    )
    args = parser.parse_args()

    gds_file = os.path.abspath(args.gds) if args.gds else find_latest_gds()
    lyp_file = os.path.abspath(args.lyp)

    if not os.path.exists(gds_file):
        print(f"[error] GDS file not found: {gds_file}")
        sys.exit(1)
    if not os.path.exists(lyp_file):
        print(f"[error] .lyp file not found: {lyp_file}")
        sys.exit(1)

    print(f"GDS : {gds_file}")
    print(f"LYP : {lyp_file}")
    print("Opening in KLayout...")

    klayout_open("-e", gds_file, "-l", lyp_file)
