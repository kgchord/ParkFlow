#!/bin/bash
# Reproduce every FEA result of cad/fea. Needs: gmsh (python), ccx 2.21, numpy, matplotlib, pyvista, xvfb-run.
# Wall time on 2 cores: about 2 h (the contact runs and the A h=8 runs dominate). Run from anywhere.
set -u
cd "$(dirname "$0")/.." || exit 1
python3 scripts/build_models.py                     # derived 12 mm plate variant of base_weldment (STEP snapshot in models/)
# ---- Case A: pole + base weldment (wind on face / diagonal), mesh sizes h = 16, 11, 8 mm at the weldment
for h in 16 11 8; do
  for dir in face diag; do
    python3 scripts/case_a.py $dir $h && python3 scripts/post_a.py results/A_${dir}_t16_eq_h$h
  done
done
python3 scripts/case_a.py diag 11 12 && python3 scripts/post_a.py results/A_diag_t12_eq_h11       # 12 mm plate sensitivity
python3 scripts/case_a.py face 11 16 solid && python3 scripts/post_a.py results/A_face_t16_solid_h11  # solid-pole stiffness sensitivity
# ---- Case B: antenna bracket, 3 supports x 3 mesh sizes (+ modal)
for h in 8 6 4; do
  python3 scripts/case_b.py $h --arm;  python3 scripts/post_b.py results/B_arm_h$h
  python3 scripts/case_b.py $h;        python3 scripts/post_b.py results/B_washer_h$h
done
for h in 8 6 5; do python3 scripts/case_b.py $h --contact; python3 scripts/post_b.py results/B_contact_h$h; done
python3 scripts/case_b.py 6 --arm --freq; python3 scripts/post_freq.py results/B_arm_h6_freq
# ---- Case C: boom shell model, 5 mesh sizes x 2 loads
for s in 20 12 8 6 4; do
  for m in vert horiz; do python3 scripts/case_c.py $m $s && python3 scripts/post_c.py results/C_boom_${m}_s$s; done
done
python3 scripts/summarize.py                         # results/summary.json + figures/convergence_*.png
xvfb-run -a python3 scripts/render_all.py            # figures/vm_*.png (1920 px wide)
bash scripts/pack.sh                                 # compress results (frd/inp/dat -> .gz)
