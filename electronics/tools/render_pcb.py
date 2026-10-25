#!/usr/bin/env python3
"""Render the placement-only board with matplotlib: outline, pads, footprint bounding boxes, reference designators,
net-class coloured ratsnest (minimum spanning tree per net), zone labels. Reads lane_controller.kicad_pcb via pcbnew.
Usage: render_pcb.py <out.png> [side=F|B|both]"""
import sys, os, math, collections
import pcbnew
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

KDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kicad'))
PCB = os.path.join(KDIR, 'lane_controller.kicad_pcb')
out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/pcb_render.png'
b = pcbnew.LoadBoard(PCB)
mm = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox(); X0, Y0, X1, Y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
CLS = {'Power_24V_Motor': '#d62728', 'Power_24V': '#ff7f0e', 'Power_5V': '#e377c2', 'Power_3V3': '#17becf', 'GND': '#bbbbbb', 'Default': '#4a6fa5'}
ZONES = [('24 V / MOTOR POWER ZONE', 0, 0, 38, 68, '#fdecea'), ('LOGIC / ESP32-S3', 38, 7, 87, 67, '#eaf3fb'),
         ('FIELD / EDGE CONNECTORS', 0, 67, 100, 80, '#eef6ee'), ('ANTENNA KEEP-OUT', 38, 0, 86, 6.7, '#fff3c4')]

def draw(ax, side):
    ax.set_aspect('equal'); ax.set_xlim(-3, 103); ax.set_ylim(83, -4)
    ax.add_patch(Rectangle((0, 0), 100, 80, fc='#fbfbf8', ec='#222', lw=1.6, zorder=0))
    for name, x0, y0, x1, y1, col in ZONES:
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=col, ec='none', alpha=.8, zorder=0.5))
        ax.text(x0 + 0.8, y0 + 1.4, name, fontsize=5.5, color='#555', va='top', zorder=0.6)
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        if ref.startswith('H'):
            p = fp.GetPosition(); ax.add_patch(plt.Circle((mm(p.x) - X0, mm(p.y) - Y0), 1.6, fc='white', ec='#222', lw=1, zorder=3)); continue
        on_b = fp.IsFlipped()
        if side != 'both' and (on_b != (side == 'B')): 
            r = fp.GetBoundingBox(False, False)
            ax.add_patch(Rectangle((mm(r.GetX()) - X0, mm(r.GetY()) - Y0), mm(r.GetWidth()), mm(r.GetHeight()), fc='none', ec='#d9d9d9', lw=.3, ls=':', zorder=1))
            continue
        r = fp.GetBoundingBox(False, False)
        if ref == 'U4':   # draw the module body, not the 48x41 keep-out courtyard
            c = fp.GetPosition(); cx, cy = mm(c.x) - X0, mm(c.y) - Y0; rx, ry, rw, rh = cx - 9.2, cy - 12.9, 18.4, 25.8
        else:
            rx, ry, rw, rh = mm(r.GetX()) - X0, mm(r.GetY()) - Y0, mm(r.GetWidth()), mm(r.GetHeight())
        ax.add_patch(Rectangle((rx, ry), rw, rh, fc='#ffffff', ec='#6b4f00' if not on_b else '#006b6b', lw=.5, alpha=.85, zorder=2))
        for pad in fp.Pads():
            pb = pad.GetBoundingBox()
            ax.add_patch(Rectangle((mm(pb.GetX()) - X0, mm(pb.GetY()) - Y0), mm(pb.GetWidth()), mm(pb.GetHeight()), fc='#b87333' if not on_b else '#3a8f8f', ec='none', zorder=2.5))
        fs = 3.6 if max(rw, rh) < 8 else 5.5
        ax.text(rx + rw / 2, ry + rh / 2, ref + ('(B)' if on_b else ''), fontsize=fs, ha='center', va='center', color='#222', zorder=4,
                bbox=dict(boxstyle='round,pad=0.08', fc='white', ec='none', alpha=.7))
    # ratsnest: MST per net on pad centres
    nets = collections.defaultdict(list)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n and not n.startswith('unconnected'):
                p = pad.GetPosition(); nets[n].append((mm(p.x) - X0, mm(p.y) - Y0))
    ncls = {}
    for n in nets:
        ni = b.FindNet(n); ncls[n] = ni.GetNetClassName() if ni else 'Default'
    cnt = 0
    for n, pts in nets.items():
        if len(pts) < 2 or n == '/GND': continue
        pts = list(dict.fromkeys(pts)); inT = {0}; edges = []
        d = {i: (math.dist(pts[0], pts[i]), 0) for i in range(1, len(pts))}
        while d:
            i = min(d, key=lambda k: d[k][0]); edges.append((pts[d[i][1]], pts[i])); inT.add(i); del d[i]
            for j in d:
                dj = math.dist(pts[i], pts[j])
                if dj < d[j][0]: d[j] = (dj, i)
        c = CLS.get(ncls[n], CLS['Default'])
        for (a, bq) in edges:
            ax.plot([a[0], bq[0]], [a[1], bq[1]], color=c, lw=.45 if ncls[n] == 'Default' else .9, alpha=.8, zorder=3.5); cnt += 1
    return cnt

sides = ['F', 'B'] if (len(sys.argv) < 3 or sys.argv[2] == 'both') else [sys.argv[2]]
fig, axes = plt.subplots(1, len(sides), figsize=(11 * len(sides), 9.4), dpi=170)
axes = [axes] if len(sides) == 1 else list(axes)
for ax, s in zip(axes, sides):
    n = draw(ax, s)
    ax.set_title(f'ParkFlow Lane Controller Rev A - {"top (F)" if s == "F" else "bottom (B)"} side - PLACEMENT ONLY, UNROUTED (ratsnest lines, GND pours not drawn)', fontsize=8.5, loc='left')
    ax.set_xlabel('mm  (100 x 80 board)', fontsize=7); ax.tick_params(labelsize=6)
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([0], [0], color=c, lw=2, label=k) for k, c in CLS.items() if k != 'GND'], loc='lower center', ncol=5, fontsize=7, frameon=False)
fig.patch.set_facecolor('white'); plt.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(out, facecolor='white'); print('wrote', out)
