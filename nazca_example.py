import nazca as nd

# ================ # 
# Section 2 and 2nd assignment #
# ================ #

# with nd.Cell(name="top") as top:
#     # two rectangles at different positions
#     nd.strt(10).put(0, 5)
#     nd.strt(10).put(10, 10)

#     # add a rectangle to another layer
#     nd.strt(length=5, layer=1).put(20, 5, 45)

# top.put()
# nd.export_gds(filename="layout_gds/nazca_2ndAssignment.gds")

# ================ # 
# Section 3 and 3rd assignment (emoji -.-) #
# ================ #
# with nd.Cell(name="top") as top:
#     # draw a smiley face using rectangles and circles
#     nd.strt(10).put(-15, 10)  # left eye
#     nd.strt(10).put(5, 10)  # right eye
#     # nd.bend(radius=15, angle=180).put(0, 0)  # smile
#     nd.Polygon(points=nd.geometries.circle(radius=5, N=64), layer=11).put(0, 0)  # smile

# top.put()
# nd.export_gds(filename="layout_gds/nazca_3rdAssignment.gds")

# ================ # 
# Section 3 and 3rd assignment (emoji -.-) #
# ================ #
with nd.Cell(name="top") as top:
    # draw a smiley face using rectangles and circles
    nd.strt(10).put(-15, 10)  # left eye
    nd.strt(10).put(5, 10)  # right eye
    # nd.bend(radius=15, angle=180).put(0, 0)  # smile
    nd.Polygon(points=nd.geometries.circle(radius=5, N=64), layer=11).put(0, 0)  # smile

top.put()
nd.export_gds(filename="layout_gds/nazca_3rdAssignment.gds")