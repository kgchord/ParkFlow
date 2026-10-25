#!/usr/bin/env python3
"""Power tree 230 VAC -> all rails (graphviz). Numbers come from power_model.py (targets, to be bench-verified)."""
import subprocess, os, power_model as m
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'diagrams')
def box(i, label, fill='#ffffff', color='#334155', style='filled,rounded', extra=''):
    return f'{i} [label="{label}", fillcolor="{fill}", color="{color}", style="{style}" {extra}];'
NODES = '\n'.join([
box('ac',f'230 VAC mains\\n(site supply, PE bonded)','#fee2e2'),
box('mcb',f'2x MCB 1P 6 A C (Schneider A9N1P06C)\\n+ Type 2 SPD (BOM) ; RCCB 30 mA (BOM)','#fef3c7'),
box('p24',f'Mean Well LRS-200-24\\n24 V / 8.8 A, 211 W (BOM)','#ffedd5'),
box('p12',f'Mean Well LRS-100-12\\n12 V / 8.5 A, 102 W (BOM)','#ffedd5'),
box('poe',f'Netgear GS305P adapter\\n63 W PoE budget (BOM)','#ffedd5'),
box('b24',f'24 V DC bus\\ntyp {m.b24_typ:.1f} A, coincident peak {m.b24_pk:.1f} A\\n({100*m.b24_pk/m.PSU_A:.0f} % of 8.8 A; 7.15 A would have been the\\nLRS-150 hiccup point)','#fecaca','#b91c1c'),
box('mot',f'K1 contactor LC1D09BD + IBT-2 module (2x BTS7960)\\nBarrier motor Lucas TVS 24 V\\ntyp {m.b24[0][1]:.1f} A, peak {m.b24[0][2]:.1f} A (limit)'),
box('f1',f'F1 3 A very fast (0451003.MRL)\\nQ1 reverse-polarity P-FET, D2 SMBJ33A'),
box('u1',f'TPS54560 24 V > 5 V\\ntyp {m.v5_typ:.1f} A, peak {m.v5_pk:.1f} A (5 A rated)'),
box('u2',f'TLV62569 5 V > 3.3 V\\nESP32-S3-WROOM-1-N16R8, logic'),
box('p10',f'P10 sign (J13) + WS2812 ring (J10)\\n5 V, peak 3.0 A + 0.18 A'),
box('fld',f'F2 MF-R075 0.75 A hold\\n24 V field: optos, beam, buzzer, E-stop loop'),
box('xl',f'XL4015 24 V > 5.1 V (BOM)\\nPi 5 feed, peak {m.edge24_pk:.1f} A at 24 V'),
box('x12',f'Geekworm X1202 UPS, 2x 18650\\nusable {m.ups_use:.1f} Wh vs {m.ups_need:.1f} Wh for 10 min = {m.ups_margin:.1f}x'),
box('pi',f'Raspberry Pi 5 + AI HAT+\\n5.1 V, typ 8 W, peak 20 W'),
box('rf',f'ID Tech IDT 85 RFID (9-12 VDC)\\ntyp {m.b12[0][1]:.1f} A, peak {m.b12[0][2]:.1f} A'),
box('mu',f'12 V mini DC UPS (Enerva, 27.5 Wh)\\nride-through {m.mini_margin:.1f}x for 10 min'),
box('cam',f'CP Plus CP-UNC-TD21ZL6C (PoE)\\n802.3af class, target <= 15.4 W'),
box('bk',f'Optional 24 V battery buffer (not in BOM)\\nbaseline = fail-in-place + manual release,\\nsee docs/OPEN_DECISIONS.md','#ffffff','#b91c1c','dashed,rounded', ', fontcolor="#b91c1c"')
])
g = f'''digraph P {{
rankdir=TB; bgcolor="white"; nodesep=0.3; ranksep=0.55; splines=polyline;
node [shape=box, fontname="Helvetica", fontsize=11, penwidth=1.4, margin="0.12,0.07"];
edge [fontname="Helvetica", fontsize=10, color="#b91c1c", penwidth=1.6];
labelloc=t; fontname="Helvetica-Bold"; fontsize=18;
label="ParkFlow Demo Lane - power tree (BOM chain; all currents are design targets, to be bench-verified)";
{NODES}
ac -> mcb [label="230 V"];
mcb -> p24; mcb -> p12; mcb -> poe;
p24 -> b24 [label="24.0 V"];
b24 -> mot [label="via K1 (E-stop in coil loop)"];
b24 -> f1; f1 -> u1 [label="+24V"]; u1 -> u2 [label="+5V"]; u1 -> p10 [label="+5V"];
b24 -> fld [label="+24V_FIELD"];
b24 -> xl; xl -> x12 [label="5.1 V"]; x12 -> pi;
p12 -> rf [label="12 V"]; p12 -> mu [label="12 V"]; mu -> rf [style=dashed, label="on mains loss"];
poe -> cam [label="53 V PoE (assumed)"];
bk -> b24 [style=dashed, color="#b91c1c", label="missing"];
}}'''
dot = os.path.join(OUT, 'power_tree.dot'); open(dot, 'w').write(g)
subprocess.check_call(['dot', '-Tpng', '-Gdpi=130', dot, '-o', os.path.join(OUT, 'power_tree.png')])
os.remove(dot); print('wrote power_tree.png')
