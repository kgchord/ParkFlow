#!/usr/bin/env bash
# Run the REAL KiCad ERC on lane_controller.kicad_sch and save the report.
#
# Why this script exists: the installed KiCad is 7.0.11, whose `kicad-cli sch` has only the `export` subcommand.
# `kicad-cli sch erc` was added in KiCad 8, so `kicad-cli sch erc ...` just prints usage and writes no report.
# KiCad 7 can still run ERC inside the eeschema GUI, so this drives eeschema headless (Xvfb + xdotool):
# open schematic -> Inspect > ERC -> Run ERC -> tick "All" severities -> Save report.
# Usage: run_erc_gui.sh <schematic dir> <report out>
set -euo pipefail
SRC=${1:-$(dirname "$0")/../kicad}; OUT=${2:-$SRC/ERC_report.txt}
W=$(mktemp -d); export HOME=$W/home DISPLAY=:97; mkdir -p "$HOME"
cp "$SRC"/lane_controller.kicad_sch "$SRC"/lane_controller.kicad_pro "$SRC"/ParkFlow.kicad_sym "$SRC"/sym-lib-table "$W"/
Xvfb :97 -screen 0 1600x1000x24 >/dev/null 2>&1 & XV=$!
trap 'kill $XV $EE 2>/dev/null || true' EXIT
sleep 2
eeschema "$W/lane_controller.kicad_sch" >/dev/null 2>&1 & EE=$!
click() { xdotool mousemove "$1" "$2" click 1; }
wait_win() { for i in $(seq 1 90); do xdotool search --name "$1" >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }
# first-run dialogs of a fresh KiCad profile (skipped automatically on a configured profile)
WAIT=12 wait_win "Configure KiCad Settings Path" && { sleep 1; click 1017 584; } || echo "no settings-path dialog"
WAIT=30 wait_win "Configure Global Symbol Library Table" && { sleep 1; click 1180 665; } || echo "no sym-lib dialog"
sleep 20                                        # schematic load
click 1038 42; WAIT=30 wait_win "Electrical Rules Checker" || { echo "ERC dialog did not open" >&2; exit 1; }; sleep 2   # ERC toolbar button
click 923 540; sleep 25                         # Run ERC
click 372 491; sleep 1                          # show All severities
click 923 491; sleep 3                          # Save...
xdotool key ctrl+a; xdotool type --delay 20 "$W/erc.rpt"; xdotool key Return; sleep 3
cp "$W/erc.rpt" "$OUT"; echo "ERC report -> $OUT"
