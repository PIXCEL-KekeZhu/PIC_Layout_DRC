#!/usr/bin/env python3
"""
klayout_Connectivity.py — GDS connectivity check using KLayout NetTracer

Uses db.NetTracerConnectivity to define which layers conduct and
db.NetTracer to trace every net in the layout.  Nets are discovered by
iterating over original shape centres as seeds; duplicate traces of the
same net are suppressed by recording the bbox centres of already-found
elements.

Reports per net:
  - number of original shapes
  - bounding-box area and dimensions
  - layers touched (useful for cross-layer via connections)
  - net label (from text shapes in the layout, if any)
  - isolated fragments (bbox area below --min-area threshold)

Usage:
  python klayout_Connectivity.py [gds_file] [--min-area N] [--open]

Defaults:
  gds_file   layout_gds/klayout_PIC_example.gds
  --min-area 0.01  (µm²)
"""

import argparse
import os
import sys
import klayout.db as db
from klayout_utils import load_env, klayout_open

load_env()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Layer configuration ────────────────────────────────────────────────────────
# (layer_number, datatype, short_name, description)
LAYER_DEFS = [
    (1, 0, "WG",    "Si waveguide core"),
    (2, 0, "CLAD",  "SiO2 cladding"),
    (3, 0, "METAL", "Metal heater / bond pads"),
]

# Same-layer connections: shapes touching on the same layer are connected.
# Format: ("L/DT",)
SAME_LAYER_CONNECTIONS = [
    ("1/0",),
    ("2/0",),
    ("3/0",),
]

# Via / cross-layer connections: (layer_a_expr, via_expr, layer_b_expr)
# Leave empty when no inter-layer vias exist.
VIA_CONNECTIONS: list[tuple[str, str, str]] = [
    # Example:
    # ("1/0", "4/0", "3/0"),   # WG ↔ contact via ↔ METAL
]

# Minimum net bounding-box area (µm²); nets below this are flagged as fragments.
DEFAULT_MIN_AREA_UM2 = 0.01


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_connectivity() -> db.NetTracerConnectivity:
    """Return a NetTracerConnectivity object from the module-level config."""
    tech = db.NetTracerConnectivity()
    for (expr,) in SAME_LAYER_CONNECTIONS:
        tech.connection(expr, expr)
    for (a, via, b) in VIA_CONNECTIONS:
        tech.connection(a, via, b)
    return tech


def find_all_nets(
    tech: db.NetTracerConnectivity,
    layout: db.Layout,
    top_cell: db.Cell,
    layer_index: int,
) -> list[list[db.NetElement]]:
    """
    Discover all nets on *layer_index* using NetTracer.

    Seeds are the integer bbox centres of every original shape on the layer.
    After each successful trace the bbox centres of the returned elements are
    added to a 'covered' set so the same net is not traced twice.

    Returns a list of nets; each net is a list of NetElement objects.
    """
    # Collect one integer-coordinate seed per original shape
    seeds: list[db.Point] = []
    it = top_cell.begin_shapes_rec(layer_index)
    while not it.at_end():
        bb = it.shape().bbox()
        cx = (bb.left + bb.right) // 2
        cy = (bb.bottom + bb.top) // 2
        seeds.append(db.Point(cx, cy))
        it.next()

    if not seeds:
        return []

    covered: set[tuple[int, int]] = set()
    nets: list[list[db.NetElement]] = []

    for seed in seeds:
        key = (seed.x, seed.y)
        if key in covered:
            continue  # already captured by a previous trace

        tracer = db.NetTracer()
        tracer.trace(tech, layout, top_cell, seed, layer_index)
        elements = list(tracer.each_element())

        # Mark every element's bbox centre as covered
        for elem in elements:
            ebb = elem.bbox()
            ecx = (ebb.left + ebb.right) // 2
            ecy = (ebb.bottom + ebb.top) // 2
            covered.add((ecx, ecy))

        # Always mark the seed itself so isolated seeds don't loop
        covered.add(key)

        nets.append(elements)

    return nets


def net_stats(elements: list[db.NetElement], dbu: float) -> dict:
    """Compute summary statistics from a list of NetElements."""
    if not elements:
        return {
            "shape_count": 0, "layers": set(),
            "bbox_area_um2": 0.0, "w_um": 0.0, "h_um": 0.0,
            "cx_um": 0.0, "cy_um": 0.0,
        }

    merged_bbox = db.Box()
    layers_hit: set[int] = set()
    for elem in elements:
        merged_bbox += elem.bbox()
        layers_hit.add(elem.layer())

    w_um  = merged_bbox.width()  * dbu
    h_um  = merged_bbox.height() * dbu
    cx_um = (merged_bbox.left + merged_bbox.right)  * 0.5 * dbu
    cy_um = (merged_bbox.bottom + merged_bbox.top) * 0.5 * dbu

    return {
        "shape_count":    len(elements),
        "layers":         layers_hit,
        "bbox_area_um2":  w_um * h_um,
        "w_um":           w_um,
        "h_um":           h_um,
        "cx_um":          cx_um,
        "cy_um":          cy_um,
    }


# ── Main check ────────────────────────────────────────────────────────────────

def check_connectivity(
    gds_file: str,
    min_area_um2: float = DEFAULT_MIN_AREA_UM2,
    open_in_klayout: bool = False,
) -> int:
    """
    Run connectivity check and return the number of isolated fragments found.
    Exit code: 0 = pass, 1 = fragments detected.
    """
    gds_file = os.path.abspath(gds_file)
    if not os.path.exists(gds_file):
        print(f"[error] GDS file not found: {gds_file}")
        sys.exit(1)

    layout = db.Layout()
    layout.read(gds_file)
    dbu = layout.dbu

    top_cell_ids = list(layout.each_top_cell())
    if not top_cell_ids:
        print("[error] No top-level cells in GDS.")
        sys.exit(1)
    top_cell = layout.cell(top_cell_ids[0])

    tech = build_connectivity()

    # ── Header ────────────────────────────────────────────────────────────────
    print("=" * 65)
    print("  KLayout NetTracer Connectivity Check")
    print("=" * 65)
    print(f"  File     : {gds_file}")
    print(f"  Top cell : {top_cell.name}")
    print(f"  DBU      : {dbu} µm/unit")
    print(f"  Min area : {min_area_um2} µm²  (nets below this are flagged)")
    print()
    print("  Layers in GDS:")
    for li in range(layout.layers()):
        if not layout.is_valid_layer(li):
            continue
        info = layout.get_info(li)
        print(f"    {info.layer:3d}/{info.datatype:<3d}  {info.name or '(unnamed)'}")
    print()
    print("  Connectivity rules:")
    for (expr,) in SAME_LAYER_CONNECTIONS:
        print(f"    same-layer : {expr}")
    for (a, via, b) in VIA_CONNECTIONS:
        print(f"    via        : {a} -- {via} -- {b}")
    print()

    total_fragments = 0

    # ── Per-layer net tracing ─────────────────────────────────────────────────
    for layer_no, datatype, name, desc in LAYER_DEFS:
        li = layout.find_layer(db.LayerInfo(layer_no, datatype))
        if li is None or li < 0:
            print(f"  [skip] {layer_no}/{datatype}  {name} — not present in GDS")
            continue

        nets = find_all_nets(tech, layout, top_cell, li)
        n_nets = len(nets)

        print(f"  Layer {layer_no}/{datatype}  [{name}]  —  {desc}")
        print(f"    Nets found : {n_nets}")

        if n_nets == 0:
            print("    (no shapes on this layer)")
            print()
            continue

        # Sort nets by bbox area descending
        nets_with_stats = [(n, net_stats(n, dbu)) for n in nets]
        nets_with_stats.sort(key=lambda x: x[1]["bbox_area_um2"], reverse=True)

        fragments = 0
        for idx, (elements, stats) in enumerate(nets_with_stats):
            layers_str = ", ".join(
                f"{layout.get_info(l).layer}/{layout.get_info(l).datatype}"
                for l in sorted(stats["layers"])
            ) if stats["layers"] else "—"

            flag = ""
            if stats["bbox_area_um2"] < min_area_um2:
                flag = "  <-- FRAGMENT"
                fragments += 1

            print(
                f"    Net {idx + 1:4d} :  "
                f"shapes = {stats['shape_count']:4d}  "
                f"bbox = {stats['w_um']:.3f} × {stats['h_um']:.3f} µm  "
                f"area = {stats['bbox_area_um2']:10.4f} µm²  "
                f"centre = ({stats['cx_um']:+.2f}, {stats['cy_um']:+.2f}) µm  "
                f"layers = [{layers_str}]"
                f"{flag}"
            )

        if fragments:
            print(f"    --> {fragments} fragment(s) on layer {name}!")
            total_fragments += fragments
        else:
            print(f"    --> OK")
        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("=" * 65)
    if total_fragments == 0:
        print("  RESULT : PASS — no isolated fragments detected")
    else:
        print(
            f"  RESULT : FAIL — {total_fragments} isolated fragment(s) "
            f"(bbox area < {min_area_um2} µm²)"
        )
    print("=" * 65)

    if open_in_klayout:
        klayout_open(gds_file)

    return total_fragments


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GDS connectivity check using KLayout NetTracer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "gds",
        nargs="?",
        default=os.path.join(BASE_DIR, "layout_gds", "klayout_PIC_example.gds"),
        help="Path to input GDS file",
    )
    parser.add_argument(
        "--min-area",
        type=float,
        default=DEFAULT_MIN_AREA_UM2,
        metavar="UM2",
        help="Flag nets whose bbox area (µm²) is below this as isolated fragments",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the GDS in KLayout after the check",
    )
    args = parser.parse_args()

    violations = check_connectivity(args.gds, args.min_area, args.open)
    sys.exit(1 if violations > 0 else 0)
