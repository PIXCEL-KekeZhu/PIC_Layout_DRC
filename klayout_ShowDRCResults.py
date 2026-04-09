#!/usr/bin/env python3
"""
Open a DRC report (.lyrdb) or DRC layers GDS in KLayout, with all matching files.
Usage:
    uv run klayout_ShowDRCResults.py <lyrdb_file>
    uv run klayout_ShowDRCResults.py <drc_layers.gds>
    uv run klayout_ShowDRCResults.py              # opens latest report in drc_outputs/
"""
import os
import sys
import glob
from klayout_utils import load_env, klayout_open

load_env()

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'drc_outputs')
GDS_DIR    = os.path.join(BASE_DIR, 'layout_gds')

def find_matching_gds(lyrdb_file: str) -> str | None:
    base = os.path.basename(lyrdb_file)
    if base.endswith('_drc.lyrdb'):
        gds_path = os.path.join(GDS_DIR, base[:-len('_drc.lyrdb')] + '.gds')
        if os.path.exists(gds_path):
            return gds_path
    return None

def find_drc_layers_gds(lyrdb_file: str) -> str | None:
    base = os.path.basename(lyrdb_file)
    if base.endswith('_drc.lyrdb'):
        drc_gds_path = os.path.join(OUTPUT_DIR, base[:-len('.lyrdb')] + '_layers.gds')
        if os.path.exists(drc_gds_path):
            return drc_gds_path
    return None

def latest_report() -> str:
    reports = glob.glob(os.path.join(OUTPUT_DIR, '*.lyrdb'))
    if not reports:
        raise FileNotFoundError(f"No .lyrdb files found in {OUTPUT_DIR}")
    return max(reports, key=os.path.getmtime)

if __name__ == "__main__":
    arg = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else latest_report()

    if not os.path.exists(arg):
        print(f"ERROR: File not found: {arg}")
        sys.exit(1)

    # If a _drc_layers.gds is passed, infer the .lyrdb from it
    if arg.endswith('_drc_layers.gds'):
        lyrdb_name = os.path.basename(arg)[:-len('_layers.gds')] + '.lyrdb'
        lyrdb = os.path.join(OUTPUT_DIR, lyrdb_name)
        if not os.path.exists(lyrdb):
            lyrdb = None
    else:
        lyrdb = arg

    gds        = find_matching_gds(lyrdb or arg)
    drc_layers = find_drc_layers_gds(lyrdb or arg) if lyrdb else arg

    cmd_args = ["-e"]
    if gds:
        print(f"Opening GDS:        {gds}")
        cmd_args.append(gds)
    if drc_layers:
        print(f"Opening DRC layers: {drc_layers}")
        cmd_args += ["-nn", drc_layers]
    if lyrdb:
        print(f"Opening report:     {lyrdb}")
        cmd_args += ["-m", lyrdb]

    klayout_open(*cmd_args)
