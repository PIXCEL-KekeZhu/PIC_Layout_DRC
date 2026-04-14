#!/usr/bin/env python3
"""
klayout_GenerateLayerProperties.py — Generate a KLayout layer properties (.lyp) file

Builds a .lyp file for this PIC process using the KLayout Python API
(lay.LayoutView + lay.LayerPropertiesNode).  The file contains two
top-level groups:

  Process Layers    — Si WG core, SiO2 cladding, Metal
  DRC Violations    — all violation layers produced by pic_drc.drc and
                      pic_freeform.drc, colour-coded by severity

Usage:
  python klayout_LayerProperties.py [--out <file.lyp>] [--open]

Defaults:
  --out  pic_process.lyp
"""

import argparse
import os
import sys
import klayout.db  as db
import klayout.lay as lay
from klayout_utils import load_env, klayout_open

load_env()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(BASE_DIR, "layout_lyp", "pic_process.lyp")

# ── Colour palette ─────────────────────────────────────────────────────────────
# All colours as 0xRRGGBB integers.

C_WG_FILL      = 0x4169E1   # royal blue    — Si waveguide fill
C_WG_FRAME     = 0x1E40A0   # dark blue     — Si waveguide border

C_CLAD_FILL    = 0xADD8E6   # light blue    — SiO2 cladding fill
C_CLAD_FRAME   = 0x5B9BD5   # medium blue   — SiO2 cladding border

C_METAL_FILL   = 0xFFD700   # gold          — Metal fill
C_METAL_FRAME  = 0xB8860B   # dark gold     — Metal border

C_DRC_ERR      = 0xFF2020   # bright red    — DRC error fill
C_DRC_ERR_FR   = 0xCC0000   # dark red      — DRC error border
C_DRC_WARN     = 0xFF8C00   # dark orange   — DRC warning fill
C_DRC_WARN_FR  = 0xCC6000   # darker orange — DRC warning border
C_DRC_INFO     = 0xFFD700   # gold          — DRC info fill
C_DRC_INFO_FR  = 0xB8860B   # dark gold     — DRC info border

# KLayout built-in dither-pattern indices
DP_SOLID       = 0    # I0  solid fill
DP_HATCH_DIAG  = 2    # I2  diagonal hatching (used for cladding)
DP_CROSS_HATCH = 5    # I5  cross-hatch

# ── Process layer definitions ──────────────────────────────────────────────────
# Each entry: (layer, datatype, name, fill_color, frame_color, dither_pattern,
#              transparent, width, description)
PROCESS_LAYERS = [
    (1, 0,  "WG",
     C_WG_FILL,   C_WG_FRAME,   DP_SOLID,      False, 1,
     "Si waveguide core"),

    (2, 0,  "CLAD",
     C_CLAD_FILL, C_CLAD_FRAME, DP_HATCH_DIAG, True,  1,
     "SiO2 cladding"),

    (3, 0,  "METAL",
     C_METAL_FILL, C_METAL_FRAME, DP_SOLID,    False, 1,
     "Metal heater / bond pads"),
]

# ── DRC violation layer definitions ───────────────────────────────────────────
# Each entry: (layer, datatype, name, fill_color, frame_color, description)
# Severity legend:
#   ERR  — hard violations (width, spacing, enclosure) → red
#   WARN — advisory checks (bend radius, coverage)     → orange
#   INFO — informational                               → gold
DRC_LAYERS = [
    # ── pic_drc.drc ───────────────────────────────────────────────────────────
    (1, 1,  "WG.S1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "WG spacing violation"),

    # ── pic_freeform.drc — waveguide width / spacing ──────────────────────────
    (1, 1,  "WG.W1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "WG width < 0.35 µm"),

    (1, 2,  "WG.W2",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "WG width > 3.0 µm"),

    (1, 3,  "WG.SP1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "WG spacing < 0.2 µm"),

    (1, 4,  "WG.A1",
     C_DRC_WARN, C_DRC_WARN_FR,
     "Sliver / orphaned fragment"),

    (1, 5,  "WG.NOTCH",
     C_DRC_WARN, C_DRC_WARN_FR,
     "Edge notch"),

    (1, 6,  "WG.AC1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Acute corner — near-zero bend radius"),

    # ── pic_freeform.drc — bend radius ────────────────────────────────────────
    (1, 10, "WG.BR1",
     C_DRC_WARN, C_DRC_WARN_FR,
     "Bend radius < 5 µm"),

    (1, 11, "WG.BR2",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Critical bend radius < 2 µm"),

    (1, 12, "WG.SP2",
     C_DRC_WARN, C_DRC_WARN_FR,
     "Bent WG spacing < 0.4 µm"),

    # ── pic_freeform.drc — cladding enclosure ─────────────────────────────────
    (2, 1,  "WG.E1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Cladding enclosure < 1.0 µm"),

    (2, 2,  "WG.E2",
     C_DRC_WARN, C_DRC_WARN_FR,
     "Bend outer cladding < 1.5 µm"),

    # ── pic_freeform.drc — rib / etch layer ───────────────────────────────────
    (4, 1,  "RIB.W1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Rib slab width < 0.5 µm"),

    (4, 2,  "RIB.OVL1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "WG core outside etch layer"),

    (4, 3,  "RIB.ENC1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Etch enclosure < 0.3 µm"),

    (4, 4,  "RIB.SP1",
     C_DRC_ERR,  C_DRC_ERR_FR,
     "Rib slab spacing < 0.3 µm"),
]


# ── Builder helpers ────────────────────────────────────────────────────────────

def make_layer_node(
    layer: int,
    datatype: int,
    name: str,
    fill_color: int,
    frame_color: int,
    dither_pattern: int = DP_SOLID,
    transparent: bool = False,
    width: int = 1,
) -> lay.LayerPropertiesNode:
    """Return a configured LayerPropertiesNode for one layer."""
    node = lay.LayerPropertiesNode()
    node.source_layer    = layer
    node.source_datatype = datatype
    node.source_cellview = 0
    node.name            = name
    node.fill_color      = fill_color
    node.frame_color     = frame_color
    node.dither_pattern  = dither_pattern
    node.transparent     = transparent
    node.width           = width
    node.visible         = True
    node.marked          = False
    node.animation       = 0
    return node


def make_group_node(name: str, expanded: bool = True) -> lay.LayerPropertiesNode:
    """Return an empty group (folder) node."""
    node = lay.LayerPropertiesNode()
    node.name     = name
    node.expanded = expanded
    return node


def build_lyp(out_path: str) -> None:
    """Build the full layer properties tree and save to *out_path*."""

    # A headless LayoutView is required to use the save_layer_props API.
    lv = lay.LayoutView(True)
    # Attach a dummy empty layout so source expressions resolve correctly.
    dummy = db.Layout()
    lv.show_layout(dummy, False)

    # ── Group 1: Process Layers ───────────────────────────────────────────────
    grp_proc = make_group_node("Process Layers", expanded=True)
    for layer, datatype, name, fill, frame, dp, transp, width, _desc in PROCESS_LAYERS:
        grp_proc.add_child(
            make_layer_node(layer, datatype, name, fill, frame, dp, transp, width)
        )
    lv.insert_layer(lv.end_layers(), grp_proc)

    # ── Group 2: DRC Violations ───────────────────────────────────────────────
    grp_drc = make_group_node("DRC Violations", expanded=True)
    for layer, datatype, name, fill, frame, _desc in DRC_LAYERS:
        grp_drc.add_child(
            make_layer_node(layer, datatype, name, fill, frame,
                            dither_pattern=DP_SOLID, transparent=False, width=1)
        )
    lv.insert_layer(lv.end_layers(), grp_drc)

    lv.save_layer_props(out_path)
    print(f"Saved: {out_path}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a KLayout layer properties (.lyp) file for this PIC process.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT,
        metavar="FILE",
        help="Output .lyp file path",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated .lyp file in KLayout with the example GDS",
    )
    args = parser.parse_args()

    out_path = os.path.abspath(args.out)
    build_lyp(out_path)

    if args.open:
        example_gds = os.path.join(BASE_DIR, "layout_gds", "klayout_PIC_example.gds")
        if os.path.exists(example_gds):
            klayout_open("-e", example_gds, "--lyp", out_path)
        else:
            klayout_open("-e", "--lyp", out_path)
