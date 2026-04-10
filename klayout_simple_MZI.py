import pya
import math

# =======================
# Parameters
# =======================
dbu = 0.001  # 1 nm

# Waveguide
wg_width = 0.5
arm_spacing = 10.0
arm_length = 200.0
delta_length = 20.0
bend_radius = 20.0

# Metal / heater
metal_width = 2.0
pad_size = 50.0
pad_offset = 30.0

# Cladding
clad_margin = 3.0

# =======================
# Layout setup
# =======================
layout = pya.Layout()
layout.dbu = dbu
top = layout.create_cell("MZI")

# Layers
l_wg    = layout.layer(pya.LayerInfo(1, 0))   # waveguide
l_clad  = layout.layer(pya.LayerInfo(2, 0))   # cladding
l_metal = layout.layer(pya.LayerInfo(20, 0))  # metal

# =======================
# Helper functions
# =======================

def to_itype(x):
    return int(x / dbu)

def straight(cell, x1, y1, x2, y2, width, layer):
    path = pya.Path(
        [pya.Point(to_itype(x1), to_itype(y1)),
         pya.Point(to_itype(x2), to_itype(y2))],
        to_itype(width)
    )
    cell.shapes(layer).insert(path)

def bend(cell, cx, cy, r, start_angle, stop_angle, width, layer, npts=32):
    pts = []
    for i in range(npts + 1):
        a = math.radians(start_angle + (stop_angle - start_angle) * i / npts)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        pts.append(pya.Point(to_itype(x), to_itype(y)))
    path = pya.Path(pts, to_itype(width))
    cell.shapes(layer).insert(path)

def rect(cell, x1, y1, x2, y2, layer):
    box = pya.Box(
        to_itype(x1), to_itype(y1),
        to_itype(x2), to_itype(y2)
    )
    cell.shapes(layer).insert(box)

# =======================
# Build MZI waveguide
# =======================

# Input
straight(top, 0, 0, 20, 0, wg_width, l_wg)

# Splitter
straight(top, 20, 0, 40, arm_spacing/2, wg_width, l_wg)
straight(top, 20, 0, 40, -arm_spacing/2, wg_width, l_wg)

# Top arm
straight(top, 40, arm_spacing/2, 40+arm_length, arm_spacing/2, wg_width, l_wg)
straight(top, 40+arm_length, arm_spacing/2,
         40+arm_length+delta_length, arm_spacing/2, wg_width, l_wg)

# Bottom arm
straight(top, 40, -arm_spacing/2, 40+arm_length, -arm_spacing/2, wg_width, l_wg)

# Bends to combiner
bend(top,
     40+arm_length+delta_length, arm_spacing/2 - bend_radius,
     bend_radius, 90, 0, wg_width, l_wg)

bend(top,
     40+arm_length, -arm_spacing/2 + bend_radius,
     bend_radius, -90, 0, wg_width, l_wg)

# Merge/output
merge_x = 40 + arm_length + delta_length + bend_radius
straight(top, merge_x, 0, merge_x+20, 0, wg_width, l_wg)

# =======================
# Heater metal (top arm)
# =======================

heater_y = arm_spacing / 2
heater_start = 40
heater_end = 40 + arm_length + delta_length

# Heater strip
rect(top,
     heater_start,
     heater_y + wg_width,
     heater_end,
     heater_y + wg_width + metal_width,
     l_metal)

# Pads
pad1_x1 = heater_start - pad_size
pad1_x2 = heater_start
pad1_y1 = heater_y + pad_offset
pad1_y2 = pad1_y1 + pad_size

rect(top, pad1_x1, pad1_y1, pad1_x2, pad1_y2, l_metal)

pad2_x1 = heater_end
pad2_x2 = heater_end + pad_size
pad2_y1 = heater_y + pad_offset
pad2_y2 = pad2_y1 + pad_size

rect(top, pad2_x1, pad2_y1, pad2_x2, pad2_y2, l_metal)

# Routing to pads
rect(top,
     heater_start - 2,
     heater_y + wg_width,
     heater_start,
     pad1_y1,
     l_metal)

rect(top,
     heater_end,
     heater_y + wg_width,
     heater_end + 2,
     pad2_y1,
     l_metal)

# =======================
# Cladding generation
# =======================

# Collect waveguide shapes
wg_region = pya.Region(top.shapes(l_wg))

# Grow region
clad_region = wg_region.sized(to_itype(clad_margin))

# Optional: remove core (pure cladding ring)
clad_only = clad_region - wg_region

# Insert cladding
top.shapes(l_clad).insert(clad_only)

# =======================
# Save GDS
# =======================
layout.write("layout_gds/mzi_full.gds")

print("Generated: mzi_full.gds")