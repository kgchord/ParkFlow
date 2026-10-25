#!/usr/bin/env bash
# Rebuild the PCB (placement only), run DRC (KiCad engine via pcbnew), render PNGs.
# NOTE: KiCad 7.0.x has no `kicad-cli pcb drc` (added in KiCad 8); DRC is run through pcbnew.WriteDRCReport in run_drc.py.
set -euo pipefail
cd "$(dirname "$0")"
python3 gen_pcb.py
python3 run_drc.py /tmp/pf_drc_raw.txt   # then paste raw output under the hand-written header of kicad/DRC_report.txt
python3 - <<'PY'
# render copies without the filled GND pours so pads and parts stay readable
import os, pcbnew
k = os.path.normpath(os.path.join(os.getcwd(), '..', 'kicad'))
b = pcbnew.LoadBoard(os.path.join(k, 'lane_controller.kicad_pcb'))
for z in list(b.Zones()): b.Remove(z)
pcbnew.SaveBoard('/tmp/pf_render_nozone.kicad_pcb', b)
PY
cd ../kicad
kicad-cli pcb export pdf -l "F.Cu,F.Silkscreen,F.Fab,Edge.Cuts" -o /tmp/pf_top.pdf /tmp/pf_render_nozone.kicad_pcb
kicad-cli pcb export pdf -l "B.Cu,B.Silkscreen,B.Fab,Edge.Cuts" --mirror -o /tmp/pf_bot.pdf /tmp/pf_render_nozone.kicad_pcb
for s in top bot; do pdftoppm -r 300 -png -singlefile /tmp/pf_$s.pdf /tmp/pf_$s; done
python3 - <<'PY'
from PIL import Image, ImageOps
for s, name in (('top', 'board_top_kicad.png'), ('bot', 'board_bottom_kicad.png')):
    im = Image.open(f'/tmp/pf_{s}.png').convert('RGB'); bb = ImageOps.invert(im).getbbox()
    im.crop((bb[0] - 30, bb[1] - 30, bb[2] + 30, bb[3] + 30)).save(f'../kicad/{name}'); print(name)
PY
cd ../tools
python3 render_pcb.py ../kicad/board_placement_ratsnest.png both
rm -f ../kicad/lane_controller.kicad_prl
