import nazca as nd
import matplotlib.pyplot as plt

# Define layers and cross-section
nd.add_layer(name='wg_layer', layer=(1, 0))
nd.add_xsection(name='wg')
nd.add_layer2xsection(xsection='wg', layer='wg_layer', leftedge=(0.5, 0), rightedge=(-0.5, 0))

# Straight waveguide cell
with nd.Cell(name='straight_wg') as straight:
    nd.strt(length=10, xs='wg').put(0)
    nd.Pin('a0').put(0, 0, 180)
    nd.Pin('b0').put(10, 0, 0)

# Bent waveguide cell (90 degrees)
with nd.Cell(name='bent_wg') as bend:
    nd.bend(angle=90, radius=5, xs='wg').put(0)

# Top-level layout: straight -> bend -> straight
with nd.Cell(name='top') as top:
    s1 = straight.put(0)
    b1 = bend.put(s1.pin['b0'])
    s2 = straight.put(b1.pin['b0'])

# Export to GDS and show layout in matplotlib
nd.export_gds(filename='layout_gds/example.gds')
nd.export_plt(topcells=top)
plt.show()
print("Exported example.gds")
