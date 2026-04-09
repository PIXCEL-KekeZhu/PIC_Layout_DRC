import nazca as nd

with nd.Cell(name="top") as top:
    nd.strt(10).put(0, 5)
    nd.strt(10).put(10, 10)
nd.strt

top.put()
nd.export_gds(filename="layout_gds/nazca_2ndAssignment.gds")