#!/usr/bin/env python3
"""Run the real KiCad DRC engine on lane_controller.kicad_pcb and write the report.
`kicad-cli pcb drc` exists only from KiCad 8; with KiCad 7.0.x the same engine is reachable from the pcbnew Python module
(pcbnew.WriteDRCReport), which is what this script uses. Usage: run_drc.py <out.txt>"""
import sys, os
os.environ.setdefault('KICAD7_FOOTPRINT_DIR', '/usr/share/kicad/footprints')
import pcbnew
KDIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kicad'))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KDIR, 'DRC_report.raw.txt')
# a fresh KiCad profile has no global footprint-library table; use KiCad's default one so 'lib_footprint_issues' is meaningful
cfg = os.path.expanduser('~/.config/kicad/7.0'); os.makedirs(cfg, exist_ok=True)
if not os.path.exists(cfg + '/fp-lib-table'):
    import shutil; shutil.copy('/usr/share/kicad/template/fp-lib-table', cfg + '/fp-lib-table')
b = pcbnew.LoadBoard(os.path.join(KDIR, 'lane_controller.kicad_pcb'))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
ok = pcbnew.WriteDRCReport(b, out, pcbnew.EDA_UNITS_MILLIMETRES, True)
print('WriteDRCReport ->', ok, out)
