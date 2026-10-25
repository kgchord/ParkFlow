#!/usr/bin/env python3
"""parse natural frequencies from a ccx *FREQUENCY .dat file -> metrics.json.  usage: post_freq.py <results/B_..._freq>"""
import sys, os, re, json
wd = sys.argv[1]
txt = open(os.path.join(wd, "job.dat")).read()
rows = re.findall(r"^\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$", txt.split("E I G E N V A L U E")[1], re.M)
freqs = [float(r[3]) for r in rows]
meta = json.load(open(os.path.join(wd, "meta.json")))
out = dict(tag=meta["tag"], h=meta["h"], elements=meta["elements"], nodes=meta["nodes"], freq_Hz=freqs[:8], f1_Hz=freqs[0])
json.dump(out, open(os.path.join(wd, "metrics.json"), "w"), indent=1)
print(out)
