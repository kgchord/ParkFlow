#!/usr/bin/env python3
"""pyvista offscreen renderer for ccx .frd results (white background, legend, deformation scale noted)."""
import os, sys, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fea_lib as fl


def load(frd):
    fr = fl.parse_frd(frd)
    grid, ids, idx = fl.frd_to_vtk(fr)
    comps, sid, svals, _ = fr["last"]["STRESS"]
    dcomps, did, dvals, _ = fr["last"]["DISP"]
    n = grid.n_points
    vm = np.zeros(n); disp = np.zeros((n, 3))
    vmv = fl.von_mises(svals[:, :6])
    for k, v in zip(sid, vmv):
        vm[idx[int(k)]] = v
    for k, v in zip(did, dvals):
        disp[idx[int(k)]] = v[:3]
    grid.point_data["vonMises_MPa"] = vm
    grid.point_data["disp"] = disp
    grid.point_data["disp_mag_mm"] = np.linalg.norm(disp, axis=1)
    return grid


def render(grid, out_png, title, clim, scale, camera=None, scalars="vonMises_MPa", cbar_title="von Mises [MPa]",
           notes=(), size=(1920, 1080), clip=None, zoom=1.0, annotate_pts=(), above_color="#7a0019", show_edges=False,
           show_undeformed=True, cmap="jet", lighting=True, subdiv=2, smooth=True):
    import pyvista as pv
    pv.OFF_SCREEN = True
    g = grid
    if clip is not None:
        g = g.clip_box(clip, invert=False)
    surf = g.extract_surface(nonlinear_subdivision=subdiv, algorithm="dataset_surface")
    defo = surf.copy(deep=True)
    defo.points = surf.points + scale * surf["disp"] if scale else surf.points
    pl = pv.Plotter(off_screen=True, window_size=list(size))
    pl.set_background("white")
    if show_undeformed and scale:
        pl.add_mesh(surf.extract_feature_edges(feature_angle=35), color="#9aa0a6", line_width=1.2, opacity=0.8)
    sb = dict(title=cbar_title, vertical=True, position_x=0.915, position_y=0.12, height=0.68, width=0.04,
              title_font_size=22, label_font_size=22, color="black", n_labels=6, fmt="%.0f")
    pl.add_mesh(defo, scalars=scalars, cmap=cmap, clim=clim, above_color=above_color, show_edges=show_edges,
                edge_color="#444444", scalar_bar_args=sb, smooth_shading=smooth, lighting=lighting)
    pl.add_text(title, position="upper_left", font_size=17, color="black", font="arial")
    y = 0.045
    for t in notes[::-1]:
        pl.add_text(t, position=(0.012, y), viewport=True, font_size=15, color="#222222", font="arial")
        y += 0.034
    for (p, lab) in annotate_pts:
        pl.add_point_labels(np.array([p]), [lab], font_size=20, point_size=14, text_color="black", shape_color="white",
                            shape_opacity=0.85, point_color="black", always_visible=True)
    if camera == "iso" or camera is None:
        pl.view_isometric()
    elif isinstance(camera, str):
        pl.camera_position = camera
    else:
        pl.camera_position = camera
    pl.camera.zoom(zoom)
    pl.screenshot(out_png)
    pl.close()
    return out_png
