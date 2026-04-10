#!/usr/bin/env python3
"""
klayout_PIC_example.py — Standard PIC layout using KLayout Python API

Components:
  - Grating couplers (input / output)
  - 1×2 MMI splitter and 2×1 MMI combiner
  - Mach-Zehnder Interferometer (MZI) with two waveguide arms
  - Thermo-optic phase shifter (metal heater stripe on upper arm)
  - Metal bond pads for voltage control of the phase shifter
  - SiO2 cladding layer covering all waveguides
  - Photodetector landing pad at output

Layers:
  1/0  Si  waveguide core
  2/0  SiO2 cladding
  3/0  Metal  (heater + bond pads)

Layout diagram (top-down, not to scale):

  y(µm)
   65 ┤   ┌──────────────┐         ┌──────────────┐
      │   │  V+ bond pad │         │ GND bond pad │
   25 ┤   │   (40×40µm)  ├─ lead ──┤   (40×40µm)  │
      │   └──────┬───────┘         └───────┬──────┘
   21 ┤          └──────── heater ──────────┘       (2µm wide metal, layer 3)
   20 ┤  ╭────────────────────────────────────────╮  upper arm (layer 1)
      │ ╱  S-bend                         S-bend  ╲
    0 ┼─░░░░░──[MMI]────────────────────[MMI]──░░░░░──[PD pad]
      │ ╲  S-bend                         S-bend  ╱
  -20 ┤  ╰────────────────────────────────────────╯  lower arm (layer 1)
      │
      └──┬─────┬──┬───┬──────────────────┬───┬──┬─────┬──┬──── x(µm)
         0    20 35  41  61           141  161 167    207 232

  Component           x-range (µm)    layer
  ─────────────────────────────────────────────────────
  Input grating coupler    0 .. 20     1/0
  Input waveguide         20 .. 35     1/0
  MMI splitter (1×2)      35 .. 41     1/0
  Diverging S-bends       41 .. 61     1/0
  Upper arm               61 ..141     1/0   y = +20
  Lower arm               61 ..141     1/0   y = -20
  Heater stripe           76 ..126     3/0   y = +20 ± 1µm
  Metal leads + V+ pad    56 .. 96     3/0   y = 25..65
  Metal leads + GND pad  106 ..146     3/0   y = 25..65
  Converging S-bends     141 ..161     1/0
  MMI combiner (2×1)     161 ..167     1/0
  Output waveguide       167 ..187     1/0
  Output grating coupler 187 ..207     1/0
  Photodetector pad      212 ..252     3/0   y = -15..+15
  SiO2 cladding (full)    -3 ..255     2/0
"""
import klayout.db as db
import math
import os

# ── Layout setup ──────────────────────────────────────────────────────────────
layout = db.Layout()
layout.dbu = 0.001          # 1 nm grid
TOP = layout.create_cell("PIC_MZI")

L_WG    = layout.layer(1, 0)
L_CLAD  = layout.layer(2, 0)
L_METAL = layout.layer(3, 0)

# ── Design parameters ─────────────────────────────────────────────────────────
HW        = 0.25    # waveguide half-width  → total width = 0.5 µm
R         = 10.0    # S-bend radius (µm)
N         = 64      # arc segments per 90° sweep
ARM_Y     = 2 * R   # arm offset from center = 20 µm  (arms at ±ARM_Y)

HEAT_HW   = 1.0     # heater half-width (2 µm wide strip)
LEAD_HW   = 0.5     # metal lead half-width
PAD_SIZE  = 40      # square bond pad side length (µm)
PAD_GAP   = 4       # gap between heater top and pad bottom
GC_HW     = 6.0     # grating coupler half-width at mouth

# ── Primitives ────────────────────────────────────────────────────────────────
def wg(x0, y0, x1, y1):
    TOP.shapes(L_WG).insert(db.DBox(x0, y0, x1, y1))

def metal(x0, y0, x1, y1):
    TOP.shapes(L_METAL).insert(db.DBox(x0, y0, x1, y1))

def bend(layer, cx, cy, r_in, r_out, a0_deg, a1_deg, n=N):
    """Annular arc polygon: outer arc a0→a1, inner arc a1→a0."""
    def pt(r, a):
        return db.DPoint(cx + r * math.cos(math.radians(a)),
                         cy + r * math.sin(math.radians(a)))
    outer = [pt(r_out, a0_deg + (a1_deg - a0_deg) * i / n) for i in range(n + 1)]
    inner = [pt(r_in,  a1_deg + (a0_deg - a1_deg) * i / n) for i in range(n + 1)]
    TOP.shapes(layer).insert(db.DPolygon(outer + inner))

# ── S-bend helpers ────────────────────────────────────────────────────────────
# All S-bends keep heading direction → (heading right throughout).

def sbend_up(x0, y0):
    """(x0, y0) → (x0+2R, y0+2R)  [CCW then CW]"""
    bend(L_WG, x0,       y0 + R, R - HW, R + HW, -90,   0)   # arc1 CCW
    bend(L_WG, x0 + 2*R, y0 + R, R - HW, R + HW,  180,  90)  # arc2 CW

def sbend_down(x0, y0):
    """(x0, y0) → (x0+2R, y0-2R)  [CW then CCW]"""
    bend(L_WG, x0,       y0 - R, R - HW, R + HW,  90,    0)  # arc1 CW
    bend(L_WG, x0 + 2*R, y0 - R, R - HW, R + HW, 180,  270)  # arc2 CCW

def sbend_up_return(x0, y0):
    """(x0, y0+2R) → (x0+2R, y0)  [CW then CCW]"""
    bend(L_WG, x0,       y0 + R, R - HW, R + HW,  90,    0)  # arc1 CW
    bend(L_WG, x0 + 2*R, y0 + R, R - HW, R + HW, 180,  270)  # arc2 CCW

def sbend_down_return(x0, y0):
    """(x0, y0-2R) → (x0+2R, y0)  [CCW then CW]"""
    bend(L_WG, x0,       y0 - R, R - HW, R + HW, 270,  360)  # arc1 CCW
    bend(L_WG, x0 + 2*R, y0 - R, R - HW, R + HW, 180,   90)  # arc2 CW

# ── Key x-coordinates (all in µm) ─────────────────────────────────────────────
#
#   [GC_IN] ─ [WG_IN] ─ [MMI_S] ── sbend_up / sbend_down ──
#                                   [ARM_START] ─────── [ARM_END]
#                                                ──── sbend_up/down_return ──
#                                                     [MMI_C] ─ [WG_OUT] ─ [GC_OUT]
#
X_GC_IN_MOUTH   = 0
X_GC_IN_END     = 20
X_WG_IN_END     = 35
X_MMI_S_START   = X_WG_IN_END          # 35
X_MMI_S_END     = X_MMI_S_START + 6    # 41
X_ARM_START     = X_MMI_S_END + 2 * R  # 61   (arms at ±ARM_Y from here)
ARM_LEN         = 80
X_ARM_END       = X_ARM_START + ARM_LEN  # 141
X_MMI_C_START   = X_ARM_END + 2 * R    # 161
X_MMI_C_END     = X_MMI_C_START + 6    # 167
X_WG_OUT_END    = X_MMI_C_END + 20     # 187
X_GC_OUT_END    = X_WG_OUT_END + 20    # 207
X_PD_CX         = X_GC_OUT_END + 25    # 232   PD pad centre

# Heater extent (on upper arm straight, with 15 µm margin each side)
HEAT_X0 = X_ARM_START + 15   # 76
HEAT_X1 = X_ARM_END   - 15   # 126

# Bond pad vertical positions (above upper arm)
PAD_YBOT = ARM_Y + HEAT_HW + PAD_GAP           # 25 µm
PAD_YTOP = PAD_YBOT + PAD_SIZE                  # 65 µm

# ═════════════════════════════════════════════════════════════════════════════
# 1.  INPUT GRATING COUPLER
#     Tapered polygon: 12 µm wide at mouth, 0.5 µm at WG tip
# ═════════════════════════════════════════════════════════════════════════════
gc_in_pts = [
    db.DPoint(X_GC_IN_MOUTH, -GC_HW),
    db.DPoint(X_GC_IN_MOUTH,  GC_HW),
    db.DPoint(X_GC_IN_END,    HW),
    db.DPoint(X_GC_IN_END,   -HW),
]
TOP.shapes(L_WG).insert(db.DPolygon(gc_in_pts))

# Grating ridges (periodic lines across the taper indicating corrugation)
PERIOD = 1.5   # µm grating period (visible at layout scale)
TOOTH  = 0.6   # tooth width
for i in range(10):
    gx = 1.0 + i * PERIOD
    if gx + TOOTH > X_GC_IN_END:
        break
    t = gx / X_GC_IN_END
    gy = GC_HW * (1 - t) + HW * t   # local half-width
    TOP.shapes(L_WG).insert(db.DBox(gx, gy, gx + TOOTH, gy + 0.5))
    TOP.shapes(L_WG).insert(db.DBox(gx, -gy - 0.5, gx + TOOTH, -gy))

# ═════════════════════════════════════════════════════════════════════════════
# 2.  INPUT WAVEGUIDE
# ═════════════════════════════════════════════════════════════════════════════
wg(X_GC_IN_END, -HW, X_WG_IN_END, HW)

# ═════════════════════════════════════════════════════════════════════════════
# 3.  1×2 MMI SPLITTER
#     3 µm wide, 6 µm long — supports TE0/TE1 coupling to split power 50/50
# ═════════════════════════════════════════════════════════════════════════════
wg(X_MMI_S_START, -1.5, X_MMI_S_END, 1.5)

# Short access tapers: narrow WG → MMI width (simplified as linear taper)
mmi_s_taper_pts = [
    db.DPoint(X_WG_IN_END - 4, -HW),
    db.DPoint(X_WG_IN_END - 4,  HW),
    db.DPoint(X_MMI_S_START,  1.5),
    db.DPoint(X_MMI_S_START, -1.5),
]
TOP.shapes(L_WG).insert(db.DPolygon(mmi_s_taper_pts))

# ═════════════════════════════════════════════════════════════════════════════
# 4.  DIVERGING S-BENDS  (MMI output → arm straights)
# ═════════════════════════════════════════════════════════════════════════════
sbend_up(X_MMI_S_END, 0)    # → upper arm  (x = X_ARM_START, y = +ARM_Y)
sbend_down(X_MMI_S_END, 0)  # → lower arm  (x = X_ARM_START, y = -ARM_Y)

# ═════════════════════════════════════════════════════════════════════════════
# 5.  ARM STRAIGHT SECTIONS
# ═════════════════════════════════════════════════════════════════════════════
wg(X_ARM_START, ARM_Y  - HW, X_ARM_END, ARM_Y  + HW)   # upper arm
wg(X_ARM_START, -ARM_Y - HW, X_ARM_END, -ARM_Y + HW)   # lower arm

# ═════════════════════════════════════════════════════════════════════════════
# 6.  PHASE SHIFTER — thermo-optic metal heater on upper arm
# ═════════════════════════════════════════════════════════════════════════════
metal(HEAT_X0, ARM_Y - HEAT_HW, HEAT_X1, ARM_Y + HEAT_HW)

# ═════════════════════════════════════════════════════════════════════════════
# 7.  METAL LEADS  (heater ends → bond pads)
# ═════════════════════════════════════════════════════════════════════════════
metal(HEAT_X0 - LEAD_HW, ARM_Y + HEAT_HW, HEAT_X0 + LEAD_HW, PAD_YBOT)  # left
metal(HEAT_X1 - LEAD_HW, ARM_Y + HEAT_HW, HEAT_X1 + LEAD_HW, PAD_YBOT)  # right

# ═════════════════════════════════════════════════════════════════════════════
# 8.  BOND PADS  (voltage control of MZI phase shifter)
#     40×40 µm — suitable for manual probing or wire bonding
# ═════════════════════════════════════════════════════════════════════════════
metal(HEAT_X0 - PAD_SIZE / 2, PAD_YBOT, HEAT_X0 + PAD_SIZE / 2, PAD_YTOP)  # V+
metal(HEAT_X1 - PAD_SIZE / 2, PAD_YBOT, HEAT_X1 + PAD_SIZE / 2, PAD_YTOP)  # GND

# ═════════════════════════════════════════════════════════════════════════════
# 9.  CONVERGING S-BENDS  (arm straights → MMI combiner)
# ═════════════════════════════════════════════════════════════════════════════
sbend_up_return(X_ARM_END, 0)    # upper arm → center
sbend_down_return(X_ARM_END, 0)  # lower arm → center

# ═════════════════════════════════════════════════════════════════════════════
# 10.  2×1 MMI COMBINER
# ═════════════════════════════════════════════════════════════════════════════
wg(X_MMI_C_START, -1.5, X_MMI_C_END, 1.5)

mmi_c_taper_pts = [
    db.DPoint(X_MMI_C_END,       1.5),
    db.DPoint(X_MMI_C_END,      -1.5),
    db.DPoint(X_MMI_C_END + 4,  -HW),
    db.DPoint(X_MMI_C_END + 4,   HW),
]
TOP.shapes(L_WG).insert(db.DPolygon(mmi_c_taper_pts))

# ═════════════════════════════════════════════════════════════════════════════
# 11.  OUTPUT WAVEGUIDE
# ═════════════════════════════════════════════════════════════════════════════
wg(X_MMI_C_END + 4, -HW, X_WG_OUT_END, HW)

# ═════════════════════════════════════════════════════════════════════════════
# 12.  OUTPUT GRATING COUPLER
# ═════════════════════════════════════════════════════════════════════════════
gc_out_pts = [
    db.DPoint(X_WG_OUT_END,  HW),
    db.DPoint(X_WG_OUT_END, -HW),
    db.DPoint(X_GC_OUT_END, -GC_HW),
    db.DPoint(X_GC_OUT_END,  GC_HW),
]
TOP.shapes(L_WG).insert(db.DPolygon(gc_out_pts))

for i in range(10):
    gx = X_WG_OUT_END + 1.0 + i * PERIOD
    if gx + TOOTH > X_GC_OUT_END:
        break
    t = (gx - X_WG_OUT_END) / (X_GC_OUT_END - X_WG_OUT_END)
    gy = HW * (1 - t) + GC_HW * t
    TOP.shapes(L_WG).insert(db.DBox(gx, gy, gx + TOOTH, gy + 0.5))
    TOP.shapes(L_WG).insert(db.DBox(gx, -gy - 0.5, gx + TOOTH, -gy))

# ═════════════════════════════════════════════════════════════════════════════
# 13.  PHOTODETECTOR LANDING PAD
#      Large metal pad at output — wire-bond target for on-chip detector
# ═════════════════════════════════════════════════════════════════════════════
PD_W, PD_H = 40, 30
metal(X_PD_CX - PD_W / 2, -PD_H / 2, X_PD_CX + PD_W / 2, PD_H / 2)

# Thin metal lead: GC output tip → PD pad
metal(X_GC_OUT_END,      -LEAD_HW,
      X_PD_CX - PD_W / 2, LEAD_HW)

# ═════════════════════════════════════════════════════════════════════════════
# 14.  SiO2 CLADDING
#      Single rectangle covering the full structure with margin on all sides
# ═════════════════════════════════════════════════════════════════════════════
CLAD_MARGIN = 3.0
x_min = X_GC_IN_MOUTH - CLAD_MARGIN
x_max = X_PD_CX + PD_W / 2 + CLAD_MARGIN
y_min = -ARM_Y - R - CLAD_MARGIN        # bottom: below lower arm loop
y_max = PAD_YTOP + CLAD_MARGIN          # top: above bond pads
TOP.shapes(L_CLAD).insert(db.DBox(x_min, y_min, x_max, y_max))

# ═════════════════════════════════════════════════════════════════════════════
# Export
# ═════════════════════════════════════════════════════════════════════════════
os.makedirs("layout_gds", exist_ok=True)
output = "layout_gds/klayout_PIC_example.gds"
layout.write(output)
print(f"Exported {output}")
print(f"  MZI arm length   : {ARM_LEN} µm")
print(f"  Phase-shifter    : {HEAT_X1 - HEAT_X0} µm  (x={HEAT_X0}..{HEAT_X1})")
print(f"  Bond pad size    : {PAD_SIZE}×{PAD_SIZE} µm")
print(f"  Total chip width : {X_PD_CX + PD_W/2:.0f} µm")
