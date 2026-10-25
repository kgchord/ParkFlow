#!/usr/bin/env bash
# ParkFlow - export STL (printed parts) and DXF (laser-cut profiles) from export_parts.scad
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
S="$HERE/openscad/export_parts.scad"
mkdir -p "$HERE/stl" "$HERE/dxf"
STL=(pole_cap cable_boot edge_pi_tray occ_base occ_cover occ_diffuser boom_tip_cap pb_post_cap)
DXF=(base_plate socket_cheek_long socket_cheek_short gusset antenna_yoke_flat antenna_tilt_flat camera_plate
     sign_bracket edge_pole_bracket edge_mount_plate edge_heat_spreader barrier_base_plate barrier_motor_plate
     barrier_bearing_plate barrier_front_panel boom_carrier_plate limit_flag photo_post_foot)
for p in "${STL[@]}"; do echo "STL $p"; openscad -q -o "$HERE/stl/$p.stl" -D "part=\"$p\"" -D '$fn=64' "$S"; done
for p in "${DXF[@]}"; do echo "DXF $p"; openscad -q -o "$HERE/dxf/$p.dxf" -D "part=\"$p\"" -D '$fn=64' "$S"; done
