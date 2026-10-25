#!/usr/bin/env bash
# ParkFlow - regenerate all PNG renders headless.
# Usage: bash cad/scripts/render.sh [quick]
#   needs openscad (2021.01+) and xvfb-run. Output -> cad/renders/
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SCAD="$HERE/openscad"; OUT="$HERE/renders"; mkdir -p "$OUT"
SIZE="${SIZE:-1920,1440}"
SCHEME="${SCHEME:-Tomorrow}"      # light background, flat colours

# r <out.png> <file.scad> <camera "rx,ry,rz"> [extra -D ...]
# Camera: gimbal rotation (rot_x, rot_y, rot_z) with --viewall --autocenter,
# orthographic projection for engineering-style views.
r() {
  local out="$1" f="$2" rot="$3"; shift 3
  echo "render $out"
  xvfb-run -a openscad -q -o "$OUT/$out" --imgsize="$SIZE" --colorscheme="$SCHEME" \
    --camera=0,0,0,"$rot",0 --viewall --autocenter --projection=o "$@" "$SCAD/$f" 2>&1 | grep -v -e "^$" -e WARNING || true
}
ISO="62,0,35"        # standard iso: tilt 62 deg, rotate 35 deg (front-left-top)
ISO_R="62,0,145"     # iso from front-right

r gantry_iso.png              gantry_assembly.scad      "$ISO"   -D explode=0
r gantry_exploded.png         gantry_assembly.scad      "$ISO"   -D explode=1 -D with_plinth=0
r edge_node_iso.png           edge_node_assembly.scad   "55,0,30"  -D explode=0
r edge_node_exploded.png      edge_node_assembly.scad   "65,0,-40" -D explode=1
r edge_node_section.png       edge_node_assembly.scad   "40,0,20"  -D section=1 -D show_hood=0
r barrier_iso.png             barrier_assembly.scad     "$ISO"   -D explode=0
r barrier_exploded.png        barrier_assembly.scad     "$ISO"   -D explode=1
r barrier_section.png         barrier_assembly.scad     "75,0,-70" -D section=1 -D with_ground=0
r occupancy_iso.png           occupancy_node_assembly.scad "118,0,35" -D explode=0
r occupancy_exploded.png      occupancy_node_assembly.scad "105,0,35" -D explode=1
r occupancy_section.png       occupancy_node_assembly.scad "95,0,8" -D section=1
r lane_layout_iso.png         lane_layout.scad          "58,0,40"
r lane_layout_top.png         lane_layout.scad          "0,0,0"
r lane_layout_approach.png  lane_layout.scad          "62,0,215"
r gantry_detail_base.png      gantry_base_weldment.scad "60,0,30"
r gantry_detail_antenna.png   gantry_antenna_bracket.scad "70,0,35"

if [[ "${1:-}" != "quick" ]]; then
  python3 "$HERE/scripts/barrier_anim.py"
fi
