#!/usr/bin/env python3
"""
Open the latest (or a specified) DRC report in KLayout.

Usage:
    python klayout_ShowDRCResults.py                      # latest report in drc_outputs/
    python klayout_ShowDRCResults.py <report.lyrdb>
    python klayout_ShowDRCResults.py <drc_layers.gds>
"""
import os
import sys
import glob
from klayout_utils import load_env, klayout_open

load_env()

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'drc_outputs')
GDS_DIR    = os.path.join(BASE_DIR, 'layout_gds')


def latest_report() -> str:
    """Return the most-recently-modified .lyrdb in drc_outputs/."""
    reports = glob.glob(os.path.join(OUTPUT_DIR, '*.lyrdb'))
    if not reports:
        raise FileNotFoundError(f"No .lyrdb files found in {OUTPUT_DIR}")
    return max(reports, key=os.path.getmtime)


def find_companion_gds(lyrdb_path: str) -> str | None:
    """
    Look for <stem>_layers.gds next to the .lyrdb in drc_outputs/.
    Works for any naming convention:
      klayout_PIC_example_drc.lyrdb         → klayout_PIC_example_drc_layers.gds
      klayout_PIC_example_pic_freeform.lyrdb → klayout_PIC_example_pic_freeform_layers.gds
    """
    stem      = os.path.splitext(os.path.basename(lyrdb_path))[0]
    candidate = os.path.join(OUTPUT_DIR, stem + "_layers.gds")
    return candidate if os.path.exists(candidate) else None


def find_source_gds(lyrdb_path: str) -> str | None:
    """
    Best-effort: find the original layout GDS in layout_gds/ whose name is a
    prefix of the lyrdb stem (e.g. 'klayout_PIC_example' inside
    'klayout_PIC_example_pic_freeform').
    Returns None if not found — the companion GDS already contains all shapes.
    """
    stem = os.path.splitext(os.path.basename(lyrdb_path))[0]
    candidates = sorted(
        glob.glob(os.path.join(GDS_DIR, '*.gds')),
        key=lambda p: len(os.path.splitext(os.path.basename(p))[0]),
        reverse=True,   # longest match first
    )
    for gds_path in candidates:
        base = os.path.splitext(os.path.basename(gds_path))[0]
        if stem.startswith(base):
            return gds_path
    return None


def show(target: str):
    if not os.path.exists(target):
        print(f"ERROR: File not found: {target}")
        sys.exit(1)

    # Normalise: if a _layers.gds is given, swap to the companion .lyrdb
    if target.endswith('_layers.gds'):
        stem  = os.path.basename(target)[:-len('_layers.gds')]
        lyrdb = os.path.join(OUTPUT_DIR, stem + '.lyrdb')
        lyrdb = lyrdb if os.path.exists(lyrdb) else None
    else:
        lyrdb = target

    companion = find_companion_gds(lyrdb or target)
    source    = find_source_gds(lyrdb or target)

    cmd_args = ["-e"]

    # Prefer the companion GDS (has original shapes + violation markers merged in)
    if companion:
        print(f"Opening DRC layers: {companion}")
        cmd_args.append(companion)
    elif source:
        print(f"Opening source GDS: {source}")
        cmd_args.append(source)

    if lyrdb:
        print(f"Opening report:     {lyrdb}")
        cmd_args += ["-m", lyrdb]

    klayout_open(*cmd_args)


if __name__ == "__main__":
    arg = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else latest_report()
    show(arg)
