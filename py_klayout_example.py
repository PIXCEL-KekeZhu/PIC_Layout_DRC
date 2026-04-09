import klayout.db as db
import math

# Create layout and top cell
layout = db.Layout()
layout.dbu = 0.001  # 1 nm resolution

top = layout.create_cell("TOP")
layer = layout.layer(1, 0)

wg_width  = 0.25   # half-width = 0.25 um (total 0.5 um)
radius    = 5.0    # bend radius in um
n_pts     = 64     # arc resolution
clad_gap  = 3.0    # cladding margin around waveguides

# --- Straight waveguide 1 (horizontal, x: 0..10) ---
top.shapes(layer).insert(db.DBox(0, -wg_width, 10, wg_width))

# --- 90-degree bend (center at (10, radius)) ---
# Arc from 270° to 360° (i.e. -90° to 0°)
cx, cy = 10.0, radius
outer, inner = [], []
for i in range(n_pts + 1):
    angle = math.radians(-90 + 90 * i / n_pts)
    outer.append(db.DPoint(cx + (radius + wg_width) * math.cos(angle),
                           cy + (radius + wg_width) * math.sin(angle)))
    inner.append(db.DPoint(cx + (radius - wg_width) * math.cos(angle),
                           cy + (radius - wg_width) * math.sin(angle)))

bend_pts = outer + list(reversed(inner))
top.shapes(layer).insert(db.DPolygon(bend_pts))

# --- Straight waveguide 2 (vertical, y: radius..radius+10) ---
x_end = cx + radius
top.shapes(layer).insert(db.DBox(x_end - wg_width, radius, x_end + wg_width, radius + 10))

# --- Cladding layer (layer 2, covers entire structure with margin) ---
clad_layer = layout.layer(2, 0)
x_min = 0         - clad_gap
y_min = -wg_width - clad_gap
x_max = x_end + wg_width + clad_gap
y_max = radius + 10 + clad_gap
top.shapes(clad_layer).insert(db.DBox(x_min, y_min, x_max, y_max))

# Save GDS
output = "py_klayout_example.gds"
layout.write(output)
print(f"Exported {output}")
