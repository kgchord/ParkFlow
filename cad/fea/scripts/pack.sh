#!/bin/bash
# Shrink results/ to < 20 MB: drop solver scratch files, gzip text outputs (frd/dat/inp). render_all.py must run BEFORE this.
cd "$(dirname "$0")/../results" || exit 1
for d in */; do
  d=${d%/}
  rm -f "$d"/job.12d "$d"/job.cvg "$d"/spooles.out "$d"/fields.npz "$d"/meta.npz 2>/dev/null
  for f in job.frd job.dat job.inp; do [ -f "$d/$f" ] && gzip -6 -f "$d/$f"; done
done
du -sh .
