#!/usr/bin/env python3
"""
Run KLayout DRC on a GDS file using drc_rules/pic_drc.drc.
Usage: uv run drc.py [gds_file]
Output reports are saved to drc_outputs/
"""
import subprocess
import sys
import os
import klayout.db as db
from klayout_utils import load_env, get_klayout_bin, klayout_open

load_env()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DRC_SCRIPT  = os.path.join(BASE_DIR, 'drc_rules', 'pic_drc.drc')
OUTPUT_DIR  = os.path.join(BASE_DIR, 'drc_outputs')

# Maps (layer, datatype) → check name, must match what pic_drc.drc outputs
DRC_LAYER_MAP = {
    (1, 1): "WG.S1 - spacing violations",
}

def postprocess_drc_gds(original_gds: str, drc_gds: str):
    """Rename DRC layers to check names and merge original GDS layers in."""
    orig = db.Layout()
    orig.read(original_gds)

    drc = db.Layout()
    drc.read(drc_gds)

    # Rename DRC result layers to check names
    for li in range(drc.layers()):
        info = drc.get_info(li)
        name = DRC_LAYER_MAP.get((info.layer, info.datatype))
        if name:
            drc.set_info(li, db.LayerInfo(info.layer, info.datatype, name))

    # Copy all original GDS layers into the DRC layout
    for orig_li in range(orig.layers()):
        orig_info = orig.get_info(orig_li)
        drc_li = drc.layer(orig_info)
        for orig_cell in orig.each_cell():
            if drc.has_cell(orig_cell.name):
                drc_cell = drc.cell(orig_cell.name)
            else:
                drc_cell = drc.create_cell(orig_cell.name)
            for shape in orig_cell.shapes(orig_li).each():
                drc_cell.shapes(drc_li).insert(shape)

    drc.write(drc_gds)
    print(f"Post-processed: layers named and original GDS merged into {drc_gds}")

def run_drc(gds_file: str):
    gds_file   = os.path.abspath(gds_file)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    base_name   = os.path.splitext(os.path.basename(gds_file))[0]
    report_file = os.path.join(OUTPUT_DIR, f"{base_name}_drc.lyrdb")
    drc_gds     = os.path.join(OUTPUT_DIR, f"{base_name}_drc_layers.gds")
    klayout_bin = get_klayout_bin()

    n_threads = os.cpu_count() or 1

    print(f"Running DRC on:  {gds_file}")
    print(f"DRC rules:       {DRC_SCRIPT}")
    print(f"Report output:   {report_file}")
    print(f"DRC layers GDS:  {drc_gds}")
    print(f"Threads:         {n_threads}")

    result = subprocess.run(
        [
            klayout_bin, "-b", "-r", DRC_SCRIPT,
            "-rd", f"input={gds_file}",
            "-rd", f"output={report_file}",
            "-rd", f"threads={n_threads}",
            "-rd", f"drc_gds={drc_gds}",
        ],
        capture_output=True, text=True
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        sys.exit(result.returncode)

    print("DRC complete.")
    postprocess_drc_gds(gds_file, drc_gds)

    # Open DRC layers GDS (contains original + violations) + report in KLayout
    print("Opening results in KLayout...")
    klayout_open("-e", drc_gds, "-m", report_file)

if __name__ == "__main__":
    gds = sys.argv[1] if len(sys.argv) > 1 else "layout_gds/example.gds"
    run_drc(gds)
