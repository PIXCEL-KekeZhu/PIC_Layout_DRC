#!/usr/bin/env python3
"""
Run KLayout DRC on a GDS file.
Usage:
  python klayout_DRCCheck.py <gds_file> [--drc <drc_script>]

Defaults:
  --drc  drc_rules/pic_drc.drc
Output reports are saved to drc_outputs/
"""
import argparse
import subprocess
import sys
import os
import klayout.db as db
from klayout_utils import load_env, get_klayout_bin, klayout_open

load_env()

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'drc_outputs')

# Per-script layer maps: (layer, datatype) → human-readable check name.
# Add an entry here whenever a DRC script outputs to a new GDS layer.
DRC_LAYER_MAPS = {
    "pic_drc.drc": {
        (1, 1): "WG.S1 - spacing violations",
    },
    "pic_freeform.drc": {
        (1, 1):  "WG.W1 - width < 0.35 um",
        (1, 2):  "WG.W2 - width > 3.0 um",
        (1, 3):  "WG.SP1 - spacing < 0.2 um",
        (1, 4):  "WG.A1 - sliver / orphaned fragment",
        (1, 5):  "WG.NOTCH - edge notch",
        (1, 6):  "WG.AC1 - acute corner (near-zero bend radius)",
        (1, 10): "WG.BR1 - bend radius < 5 um",
        (1, 11): "WG.BR2 - critical bend radius < 2 um",
        (1, 12): "WG.SP2 - bent WG spacing < 0.4 um",
        (2, 1):  "WG.E1 - cladding enclosure < 1.0 um",
        (2, 2):  "WG.E2 - bend outer cladding < 1.5 um",
        (4, 1):  "RIB.W1 - rib slab width < 0.5 um",
        (4, 2):  "RIB.OVL1 - waveguide core outside etch layer",
        (4, 3):  "RIB.ENC1 - etch enclosure < 0.3 um",
        (4, 4):  "RIB.SP1 - rib slab spacing < 0.3 um",
    },
}


def postprocess_drc_gds(original_gds: str, drc_gds: str, layer_map: dict):
    """Rename DRC violation layers and merge original GDS shapes into drc_gds."""
    if not os.path.exists(drc_gds):
        print(f"[warn] DRC GDS not found (no GDS outputs in script?): {drc_gds}")
        return

    orig = db.Layout()
    orig.read(original_gds)

    drc = db.Layout()
    drc.read(drc_gds)

    # Rename DRC result layers to check names
    for li in range(drc.layers()):
        info = drc.get_info(li)
        name = layer_map.get((info.layer, info.datatype))
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


def run_drc(gds_file: str, drc_script: str):
    gds_file   = os.path.abspath(gds_file)
    drc_script = os.path.abspath(drc_script)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_name   = os.path.splitext(os.path.basename(gds_file))[0]
    script_name = os.path.basename(drc_script)
    report_file = os.path.join(OUTPUT_DIR, f"{base_name}_{os.path.splitext(script_name)[0]}.lyrdb")
    drc_gds     = os.path.join(OUTPUT_DIR, f"{base_name}_{os.path.splitext(script_name)[0]}_layers.gds")
    klayout_bin = get_klayout_bin()
    n_threads   = os.cpu_count() or 1

    print(f"Running DRC on:  {gds_file}")
    print(f"DRC rules:       {drc_script}")
    print(f"Report output:   {report_file}")
    print(f"DRC layers GDS:  {drc_gds}")
    print(f"Threads:         {n_threads}")

    result = subprocess.run(
        [
            klayout_bin, "-b", "-r", drc_script,
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

    layer_map = DRC_LAYER_MAPS.get(script_name, {})
    postprocess_drc_gds(gds_file, drc_gds, layer_map)

    # Open DRC layers GDS (contains original + violations) + report in KLayout
    print("Opening results in KLayout...")
    klayout_open("-e", drc_gds, "-m", report_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run KLayout DRC on a GDS file.")
    parser.add_argument(
        "gds",
        nargs="?",
        default="layout_gds/klayout_PIC_example.gds",
        help="Path to input GDS file",
    )
    parser.add_argument(
        "--drc",
        default=os.path.join(BASE_DIR, "drc_rules", "pic_drc.drc"),
        help="Path to DRC rule script (default: drc_rules/pic_drc.drc)",
    )
    args = parser.parse_args()
    run_drc(args.gds, args.drc)
