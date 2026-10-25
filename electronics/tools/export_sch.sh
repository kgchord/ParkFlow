#!/usr/bin/env bash
# Regenerate schematic, netlist, PDF, SVG, PNG preview (KiCad 7.0.x CLI) and PINMAP.md
set -euo pipefail
cd "$(dirname "$0")"
python3 gen_lane_controller_sch.py                       # writes .kicad_sch, .net (kicad-cli export netlist), PINMAP.md and verifies
cd ../kicad
kicad-cli sch export pdf -o lane_controller.pdf lane_controller.kicad_sch
kicad-cli sch export svg -o . lane_controller.kicad_sch   # writes lane_controller.svg for a single sheet
pdftoppm -r 110 -png -singlefile lane_controller.pdf lane_controller_sheet
