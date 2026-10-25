#!/usr/bin/env python3
"""ParkFlow system block diagram: one model -> draw.io XML + 1920 px PNG."""
import os, html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib import font_manager

OUT = os.path.join(os.path.dirname(__file__), '..', 'diagrams')
W, H = 1920, 1235
FONT = 'Inter' if any('Inter' in f.name for f in font_manager.fontManager.ttflist) else 'DejaVu Sans'
plt.rcParams['font.family'] = FONT

# ---------------------------------------------------------------- palette
G = {  # group: (fill, stroke, title colour)
    'FW':  ('#F3EEFB', '#8E6CC8', '#5B3A99'),
    'EC':  ('#EAF3FB', '#4A86C5', '#1F5A96'),
    'AP':  ('#FDF1E6', '#D9822B', '#9A5410'),
    'MS':  ('#EDF6EE', '#4E9A5B', '#2C6B37'),
}
NODE_FILL = '#FFFFFF'
EDGE = {'data': '#1F5A96', 'power': '#C0392B', 'logic': '#6B4FA0', 'mech': '#4E9A5B', 'runs': '#8E6CC8'}

groups = {
    'FW': ('FIRMWARE / LOGIC', 30, 62, 1860, 205),
    'EC': ('ELECTRONIC CONTROLLERS', 30, 292, 1860, 410),
    'AP': ('ACTUATION / POWER', 30, 727, 1280, 440),
    'MS': ('MECHANICAL STRUCTURE', 1330, 727, 560, 440),
}

# id: (group, x, y, w, h, title, subtitle)
N = {
    # firmware (last line = where it runs)
    'f_anpr': ('FW', 55, 108, 270, 140, 'ANPR pipeline', 'Plate detector + LPRNet OCR\nHailoRT on Hailo-8 (26 TOPS)\ntarget 60-120 ms / frame\n[runs on Edge Node]'),
    'f_fuse': ('FW', 345, 108, 270, 140, 'Fusion engine', 'Indian / BH plate normalisation\nweighted edit distance\nconfidence + RSSI rules\n[runs on Edge Node]'),
    'f_db':   ('FW', 635, 108, 270, 140, 'Access list + offline queue', 'SQLite (WAL), HMAC-signed\nevents, idempotent sync\n[runs on Edge Node]'),
    'f_sync': ('FW', 925, 108, 270, 140, 'Ops / sync service', 'MQTT-TLS + HTTPS to\nmock NETC ledger, dashboard,\nattendant override\n[Edge Node <> cloud]'),
    'f_fsm':  ('FW', 1215, 108, 320, 140, 'Lane FSM firmware (ESP-IDF)', 'IDLE > DETECT > READ > FUSE >\nGRANT/FALLBACK > OPEN > CLEAR > CLOSE\nanti-crush · TWDT + ext. WDT 1.6 s\n[runs on Lane Controller]'),
    'f_occ':  ('FW', 1555, 108, 310, 140, 'Occupancy firmware', 'Modbus-RTU slave, distance\nthreshold + hysteresis,\nbay LED red / green\n[runs on ESP32-C3 nodes]'),
    # electronic controllers
    'c_cam':  ('EC', 55, 345, 250, 110, 'ANPR camera', 'CP Plus CP-UNC-TD21ZL6C, 2 MP IR\nRTSP, WDR; PoE to be confirmed'),
    'c_poe':  ('EC', 55, 580, 250, 95, 'PoE switch', 'Netgear GS305P\n802.3af/at, 63 W PoE budget'),
    'c_edge': ('EC', 390, 345, 330, 215, 'EDGE NODE', 'Raspberry Pi 5 8 GB\n+ Raspberry Pi AI HAT+\n(Hailo-8, 26 TOPS, PCIe Gen3 x1)\n128 GB microSD (no NVMe), 0-50 °C\nalt: Jetson Orin Nano Super'),
    'c_wan':  ('EC', 390, 600, 170, 75, 'Uplink', '4G router / site LAN\n(lane runs offline)'),
    'c_lc':   ('EC', 820, 345, 340, 205, 'LANE CONTROLLER PCB', 'ESP32-S3-WROOM-1-N16R8\nTHVD1450 RS485 · IBT-2 header\n(74AHCT1G08 interlocks)\n7x opto inputs · TPS3823 watchdog\nTPS54560 24>5 V · TLV62569 5>3.3 V\nHUB12 / WS2812 via 74HCT245'),
    'c_io':   ('EC', 1255, 345, 270, 95, 'Field safety I/O', 'Through-beam pair 300 mm\n(BOM: Delta PS-MT5)\n2x limit switch ME-8108 (NC)'),
    'c_sign': ('EC', 1255, 468, 270, 75, 'P10 LED sign', '320x160 mm, HUB12, 5 V'),
    'c_rfid': ('EC', 1255, 575, 270, 105, 'UHF RFID reader', 'ID Tech IDT 85, 9-12 VDC, 865-867 MHz\nRS485, IP65: to be confirmed with OEM\n(Wiegand / TCP per Stage 1 brief)\ntarget read range >= 6 m'),
    'c_occ':  ('EC', 1600, 345, 265, 150, 'Occupancy nodes x4', 'ESP32-C3 SuperMini + VL53L1X ToF\n(A02YYUW ultrasonic = alternative)\nWS2812 bay LED\nRS485 link: transceivers not in BOM'),
    # actuation / power
    'p_48v':  ('AP', 55, 780, 230, 75, 'DDR-120B-48', '24 > 53.5 V / 2.5 A (PoE)\n[design intent, not in BOM]'),
    'p_5v':   ('AP', 560, 780, 230, 75, 'DDR-30G-5', '24 > 5.1 V / 6 A (Edge Node)\n[BOM: XL4015 5 A buck]'),
    'p_12v':  ('AP', 1065, 780, 225, 75, 'DDR-60G-12', '24 > 12 V / 5 A (RFID, occ.)\n[BOM: LRS-100-12 from mains]'),
    'p_ac':   ('AP', 55, 945, 200, 95, '230 VAC mains', '2x MCB 1P 6 A C (xC60)\nSPD Type 2, PE bond'),
    'p_ups':  ('AP', 300, 945, 250, 100, 'DC UPS PSU', 'Mean Well DRS-240-24 (not in BOM;\nBOM: LRS-200-24, no UPS function)\n24 V / 10 A, AC-OK / BAT-OK relays'),
    'p_bat':  ('AP', 300, 1070, 250, 75, 'Battery', '2x 12 V 12 Ah VRLA in series\nfused 15 A [not in BOM]'),
    'p_k1':   ('AP', 790, 945, 235, 95, 'K1 contactor + E-stop', 'LC1D09BD, 24 VDC coil (design intent)\nBOM: same LC1D09BD + ProMax E-stop'),
    'p_hb':   ('AP', 1065, 945, 225, 80, 'H-bridge module', 'IBT-2 (2x BTS7960) module\nPWM from ESP32-S3 via 74AHCT1G08'),
    'p_mot':  ('AP', 1065, 1055, 225, 90, 'Barrier motor', 'Lucas TVS 24 V wiper motor,\n18 N·m worm gear (BOM)'),
    # mechanical
    'm_pole': ('MS', 1350, 775, 255, 95, 'Lane gantry pole', '80x80 Al T-slot, 2.4 m\n250x250x16 base, 4x M12'),
    'm_brk':  ('MS', 1350, 890, 255, 75, 'Sensor mounts', 'RFID bracket @ 1.5 m\ncamera arm @ 1.2 m, 15-25°'),
    'm_boom': ('MS', 1350, 1000, 255, 145, 'Demo boom barrier', '1.2 m Al rect. tube boom,\ncounterweight, breakaway\nshear pin, limit flags\n0° / 90°'),
    'm_enc':  ('MS', 1625, 775, 245, 120, 'IP65 wall enclosure', 'DIN rail, M20/M25 glands,\nvent, heat spreader\n(Edge, PSU, LC, PoE)'),
    'm_ceil': ('MS', 1625, 915, 245, 80, 'Ceiling / sign mounts', 'occupancy node brackets,\nP10 sign frame'),
}

BUS_Y = 900
EXTRA_LINES = [  # (points, kind, label, label_xy)
    ([(170, BUS_Y), (1180, BUS_Y)], 'power', '24 V DC bus  (UPS output; 20.9-27.6 V on battery)', (720, BUS_Y)),
]
def anchor(nid, side, f=0.5):
    g, x, y, w, h, *_ = N[nid]
    return {'L': (x, y + h * f), 'R': (x + w, y + h * f), 'T': (x + w * f, y), 'B': (x + w * f, y + h)}[side]

# edges: (src, side, frac, dst, side, frac, label, kind, via(list of points) , label_pos (seg index or xy))
E = [
    # data / comms
    ('c_cam', 'B', .5, 'c_poe', 'T', .5, 'Ethernet + PoE 802.3at\n48-57 V · RTSP H.264', 'data', [], None),
    ('c_poe', 'R', .4, 'c_edge', 'L', .9, 'GbE', 'data', [], (347, 560)),
    ('c_wan', 'T', .5, 'c_edge', 'B', .23, 'MQTT-TLS', 'data', [], (520, 580)),
    ('c_edge', 'R', .25, 'c_lc', 'L', .27, 'UART 3.3 V TTL\n921.6 kbaud\n+ EN/BOOT', 'data', [], (770, 399)),
    ('c_edge', 'T', .9, 'c_occ', 'T', .5, 'RS485 Modbus-RTU, 19.2 kbaud (USB-RS485 on Edge Node)  +  12 V  — one 4-core cable, daisy-chain', 'data',
     [(687, 320), (1732, 320)], (1230, 320)),
    ('c_io', 'L', .5, 'c_lc', 'R', .2, '24 V opto in\n(NC fail-safe)', 'logic', [], (1207, 375)),
    ('c_lc', 'R', .6, 'c_sign', 'L', .5, 'HUB12 5 V', 'data', [], (1207, 488)),
    ('c_lc', 'R', .93, 'c_rfid', 'L', .4, 'RS485\n115.2 kbaud\nA / B / 0V', 'data', [], (1207, 590)),
    # power from converters up to loads
    ('p_48v', 'T', .5, 'c_poe', 'B', .5, '53.5 V DC', 'power', [], (170, 715)),
    ('p_5v', 'T', .45, 'c_edge', 'B', .83, '5.1 V / 5 A USB-C\n(PSU_MAX_CURRENT=5000)', 'power', [(663, 700)], (663, 700)),
    ('p_12v', 'T', .7, 'c_rfid', 'B', .1, '12 V DC', 'power', [], (1222, 715)),
    # bus taps
    ('p_ac', 'R', .5, 'p_ups', 'L', .5, '230 VAC', 'power', [], None),
    ('p_ups', 'T', .5, 'p_48v', 'B', .5, '', 'power', [(425, BUS_Y), (170, BUS_Y)], None),
    ('p_ups', 'T', .5, 'p_5v', 'B', .5, '', 'power', [(425, BUS_Y), (675, BUS_Y)], None),
    ('p_ups', 'T', .5, 'p_12v', 'B', .5, '', 'power', [(425, BUS_Y), (1177, BUS_Y)], None),
    ('p_ups', 'B', .5, 'p_bat', 'T', .5, '', 'power', [], None),
    ('p_ups', 'T', .5, 'p_k1', 'T', .75, '', 'power', [(425, BUS_Y), (966, BUS_Y)], None),
    ('p_ups', 'T', .5, 'c_lc', 'B', .62, '24 V logic\n3 A fuse', 'power', [(425, BUS_Y), (1031, BUS_Y)], (1031, 640)),
    ('c_lc', 'B', .2, 'p_k1', 'T', .27, 'K1 coil 24 V\nvia E-stop NC loop', 'logic', [], (888, 640)),
    ('p_k1', 'R', .5, 'p_hb', 'L', .5, '24 V\nmotor', 'power', [], (1045, 985)),
    ('p_hb', 'B', .5, 'p_mot', 'T', .5, 'PWM ±24 V', 'power', [], (1177, 1040)),
    # mechanical
    ('p_mot', 'R', .5, 'm_boom', 'L', .62, 'shaft >\nboom hub', 'mech', [], (1320, 1100)),
    ('m_brk', 'T', .5, 'm_pole', 'B', .5, '', 'mech', [], None),
]

def route(e):
    s, ss, sf, d, ds, df, lab, kind, via, lp = e
    p0 = anchor(s, ss, sf); p1 = anchor(d, ds, df)
    pts = [p0] + list(via) + [p1]
    if not via:
        # orthogonal Z route
        if ss in 'LR' and ds in 'LR':
            mx = (p0[0] + p1[0]) / 2
            pts = [p0, (mx, p0[1]), (mx, p1[1]), p1] if abs(p0[1] - p1[1]) > 1 else [p0, p1]
        elif ss in 'TB' and ds in 'TB':
            my = (p0[1] + p1[1]) / 2
            pts = [p0, (p0[0], my), (p1[0], my), p1] if abs(p0[0] - p1[0]) > 1 else [p0, p1]
        else:
            pts = [p0, (p1[0], p0[1]), p1] if ss in 'LR' else [p0, (p0[0], p1[1]), p1]
    return pts

# ---------------------------------------------------------------- PNG
def png(path):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis('off')
    fig.patch.set_facecolor('#FBFBFA')
    ax.text(30, 36, 'ParkFlow Demo Lane — System Block Diagram', fontsize=21, weight='bold', color='#1d2733', va='center')
    ax.text(1890, 36, 'all figures are design targets, to be bench-verified  ·  power chain = design intent, see ESDS "Inconsistencies found" #1',
            fontsize=10.5, color='#5a6470', va='center', ha='right')
    for k, (title, x, y, w, h) in groups.items():
        f, st, tc = G[k]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=14', fc=f, ec=st, lw=1.6, zorder=0))
        ax.text(x + 16, y + 20, title, fontsize=12.5, weight='bold', color=tc, va='center', zorder=1)
    for pts, kind, lab, (lx, ly) in EXTRA_LINES:
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=EDGE[kind], lw=4.5, zorder=2.5, solid_capstyle='butt')
        ax.text(lx, ly, lab, fontsize=9.2, weight='bold', color=EDGE[kind], ha='center', va='center', zorder=6,
                bbox=dict(boxstyle='round,pad=0.25', fc='#FDF1E6', ec='none'))
    for e in E:
        pts = route(e); kind = e[7]
        xs, ys = zip(*pts)
        ls = '--' if kind in ('runs', 'mech') else '-'
        lw = 2.2 if kind == 'power' else 1.6
        ax.plot(xs, ys, color=EDGE[kind], lw=lw, ls=ls, zorder=2, solid_capstyle='round')
        # arrow head on last segment
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        ax.annotate('', xy=(x1, y1), xytext=(x0 + (x1 - x0) * 0.6, y0 + (y1 - y0) * 0.6),
                    arrowprops=dict(arrowstyle='-|>', color=EDGE[kind], lw=lw, mutation_scale=14), zorder=3)
        lab = e[6]
        if lab:
            if e[9]:
                lx, ly = e[9]
            else:
                segs = list(zip(pts[:-1], pts[1:]))
                a, b = max(segs, key=lambda sg: abs(sg[0][0] - sg[1][0]) + abs(sg[0][1] - sg[1][1]))
                lx, ly = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            ax.text(lx, ly, lab, fontsize=8.6, color=EDGE[kind], ha='center', va='center', zorder=6, linespacing=1.15,
                    bbox=dict(boxstyle='round,pad=0.22', fc='white', ec=EDGE[kind], lw=0.6, alpha=0.96))
    for nid, (g, x, y, w, h, t, sub) in N.items():
        f, st, tc = G[g]
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=8', fc=NODE_FILL, ec=st, lw=1.4, zorder=4))
        ax.add_patch(FancyBboxPatch((x, y), w, 26, boxstyle='round,pad=0,rounding_size=8', fc=st, ec=st, lw=0, zorder=4.1))
        ax.add_patch(plt.Rectangle((x, y + 14), w, 12, fc=st, ec='none', zorder=4.15))
        ax.text(x + w / 2, y + 13, t, fontsize=10.4, weight='bold', color='white', ha='center', va='center', zorder=5)
        tag = None
        lines = sub.split('\n')
        if lines[-1].startswith('['):
            tag = lines.pop()[1:-1]
        body = '\n'.join(lines)
        cy = y + 26 + (h - 26) / 2 - (9 if tag else 0)
        ax.text(x + w / 2, cy, body, fontsize=9.0, color='#26313d', ha='center', va='center', zorder=5, linespacing=1.3)
        if tag:
            ax.text(x + w / 2, y + h - 13, tag, fontsize=8.6, style='italic', color=tc, ha='center', va='center', zorder=5)
    # legend
    lx, ly = 40, 1205
    ax.text(lx, ly, 'Links:', fontsize=9.5, weight='bold', color='#333', va='center')
    items = [('data', '-', 'data / comms'), ('power', '-', 'power (V shown)'), ('logic', '-', 'discrete I/O'), ('runs', '--', 'runs on'), ('mech', '--', 'mechanical')]
    cx = lx + 50
    for k, ls, t in items:
        ax.plot([cx, cx + 26], [ly, ly], color=EDGE[k], lw=2.2, ls=ls)
        ax.text(cx + 32, ly, t, fontsize=9, va='center', color='#333')
        cx += 32 + len(t) * 6.2 + 22
    ax.text(1890, 1205, 'Generated from electronics/tools/gen_system_block.py  ·  editable copy: system_block_diagram.drawio', fontsize=8.5, color='#8a929c', ha='right', va='center')
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    print('wrote', path)

# ---------------------------------------------------------------- draw.io
def drawio(path):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    esc = lambda s: html.escape(s, quote=True).replace('\n', '&#xa;')
    cells.append(f'<mxCell id="title" value="{esc("ParkFlow Demo Lane — System Block Diagram")}" style="text;html=0;fontSize=22;fontStyle=1;align=left;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="30" y="18" width="900" height="36" as="geometry"/></mxCell>')
    for k, (title, x, y, w, h) in groups.items():
        f, st, tc = G[k]
        cells.append(f'<mxCell id="g_{k}" value="{esc(title)}" style="rounded=1;arcSize=3;whiteSpace=wrap;html=0;fillColor={f};strokeColor={st};strokeWidth=2;fontColor={tc};fontStyle=1;fontSize=14;verticalAlign=top;align=left;spacingLeft=12;container=1;collapsible=0;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for nid, (g, x, y, w, h, t, sub) in N.items():
        gx, gy = groups[g][1], groups[g][2]
        f, st, tc = G[g]
        val = esc(t + '\n' + sub)
        cells.append(f'<mxCell id="{nid}" value="{val}" style="rounded=1;arcSize=6;whiteSpace=wrap;html=0;fillColor=#FFFFFF;strokeColor={st};strokeWidth=1.5;fontSize=11;fontColor=#26313d;" vertex="1" parent="g_{g}"><mxGeometry x="{x - gx}" y="{y - gy}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    for i, e in enumerate(E):
        s, ss, sf, d, ds, df, lab, kind, via, lp = e
        col = EDGE[kind]
        dash = 'dashed=1;' if kind in ('runs', 'mech') else ''
        sw = 2.5 if kind == 'power' else 1.5
        ex = {'L': 0, 'R': 1}.get(ss, sf); ey = {'T': 0, 'B': 1}.get(ss, sf)
        nx = {'L': 0, 'R': 1}.get(ds, df); ny = {'T': 0, 'B': 1}.get(ds, df)
        pts = ''.join(f'<mxPoint x="{px}" y="{py}"/>' for px, py in via)
        arr = f'<Array as="points">{pts}</Array>' if via else ''
        cells.append(f'<mxCell id="e{i}" value="{esc(lab)}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;strokeColor={col};strokeWidth={sw};{dash}fontSize=10;fontColor={col};labelBackgroundColor=#FFFFFF;exitX={ex};exitY={ey};exitDx=0;exitDy=0;entryX={nx};entryY={ny};entryDx=0;entryDy=0;endArrow=block;endFill=1;" edge="1" parent="1" source="{s}" target="{d}"><mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')
    for j, (pts, kind, lab, _) in enumerate(EXTRA_LINES):
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        cells.append(f'<mxCell id="bus{j}" value="{esc(lab)}" style="endArrow=none;html=0;strokeColor={EDGE[kind]};strokeWidth=5;fontSize=11;fontStyle=1;fontColor={EDGE[kind]};labelBackgroundColor=#FDF1E6;" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x0}" y="{y0}" as="sourcePoint"/><mxPoint x="{x1}" y="{y1}" as="targetPoint"/></mxGeometry></mxCell>')
    xml = ('<mxfile host="app.diagrams.net" modified="2026-10-24T00:00:00.000Z" agent="ParkFlow generator" version="24.7.17">\n'
           '  <diagram id="parkflow-system" name="ParkFlow System">\n'
           f'    <mxGraphModel dx="1920" dy="{H}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0">\n'
           '      <root>\n        ' + '\n        '.join(cells) + '\n      </root>\n    </mxGraphModel>\n  </diagram>\n</mxfile>\n')
    open(path, 'w').write(xml)
    print('wrote', path)

if __name__ == '__main__':
    png(os.path.join(OUT, 'system_block_diagram.png'))
    drawio(os.path.join(OUT, 'system_block_diagram.drawio'))
