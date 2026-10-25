#!/usr/bin/env python3
"""Collect metrics.json of all runs -> results/summary.json, convergence_*.png (1920 px wide) and a markdown results table."""
import os, sys, json, glob, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RES = os.path.join(ROOT, "results"); FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)

def load(pattern):
    out = []
    for d in sorted(glob.glob(os.path.join(RES, pattern))):
        f = os.path.join(d, "metrics.json")
        if os.path.exists(f):
            out.append((os.path.basename(d), json.load(open(f))))
    return out

C_RAW, C_DES, C_ALT, C_REF = "#c0392b", "#0b5ea8", "#2a9d8f", "#555555"
plt.rcParams.update({"font.size": 15, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#dddddd", "grid.linewidth": 0.8, "figure.facecolor": "white", "axes.facecolor": "white"})

def finish(fig, name):
    fig.savefig(os.path.join(FIG, name), dpi=120, facecolor="white")      # 16 in x 120 dpi = 1920 px wide
    plt.close(fig)

def lab(ax, x, y, text, color, dy=0, ha="left"):
    ax.annotate(text, (x, y), xytext=(6 if ha == "left" else -6, dy), textcoords="offset points", color=color, fontsize=13,
                va="center", ha=ha)

# ------------------------------------------------------------------ A
A = {}
for tag, m in load("A_*_t16_eq_h*"):
    A.setdefault(m["direction"], []).append(m)
if A:
    fig, ax = plt.subplots(1, 2, figsize=(16, 6.2))
    for dirn, ls in (("face", "-"), ("diag", "--")):
        L = sorted(A.get(dirn, []), key=lambda m: m["elements"])
        if not L: continue
        n = [m["elements"] for m in L]
        ax[0].plot(n, [m["weldment_raw_max"] for m in L], marker="o", mfc="white", color=C_RAW, ls=ls, lw=2)
        ax[0].plot(n, [m["weldment_design_max"] for m in L], marker="o", color=C_DES, ls=ls, lw=2.4)
        ax[1].plot(n, [m["pole_top_disp_along_wind_mm"] for m in L], marker="o", color=C_DES, ls=ls, lw=2.4)
        ax[0].annotate(dirn, (n[-1], L[-1]["weldment_design_max"]), xytext=(8, 0), textcoords="offset points", color=C_DES, fontsize=13)
    ax[0].axhline(250, color=C_REF, lw=1.2, ls=":"); ax[0].text(ax[0].get_xlim()[0] * 1.02, 255, "E250 yield 250 MPa", color=C_REF, fontsize=12)
    ax[0].set_xscale("log"); ax[0].set_yscale("log")
    ax[0].set_xlabel("elements (tet10, whole model)"); ax[0].set_ylabel("max von Mises, weldment [MPa]")
    ax[0].set_title("Peak stress vs mesh: red = raw nodal peak (weld-toe singularity, grows),\nblue = design reading outside singular zones", fontsize=14, loc="left")
    ax[1].axhline(25.96, color=C_REF, lw=1.5, ls=":"); ax[1].text(ax[1].get_xlim()[0] * 1.02, 26.1, "hand calc 25.96 mm", color=C_REF, fontsize=12)
    ax[1].set_xscale("log"); ax[1].set_xlabel("elements (tet10, whole model)"); ax[1].set_ylabel("pole-top displacement along wind [mm]")
    ax[1].set_title("Displacement vs mesh (solid: wind on face, dashed: diagonal)", fontsize=14, loc="left")
    ax[1].set_ylim(0, 30)
    fig.suptitle("CASE A  pole + base weldment, Delhi design gust 47 m/s", fontsize=17, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94)); finish(fig, "convergence_A_pole_base.png")

# ------------------------------------------------------------------ B
for supp, title in (("washer", "recipe R2 literal (washer-only support)"), ("contact", "arm-face contact + bolts"), ("arm", "arm face fixed")):
    L = sorted([m for t, m in load(f"B_{supp}_h*") if not t.endswith("_freq")], key=lambda m: m["elements"])
    if len(L) < 1: continue
    fig, ax = plt.subplots(1, 2, figsize=(16, 6.2))
    n = [m["elements"] for m in L]
    ax[0].plot(n, [m["raw_max"] for m in L], marker="o", mfc="white", color=C_RAW, lw=2)
    ax[0].plot(n, [m["design_max"] for m in L], marker="o", color=C_DES, lw=2.4)
    ax[0].plot(n, [m["yoke_bend_root_max"] for m in L], marker="s", color=C_ALT, lw=2.4)
    ax[0].axhline(10.5, color=C_REF, lw=1.2, ls=":"); ax[0].text(n[0], 10.9, "hand calc bend root 10.5 MPa", color=C_REF, fontsize=12)
    ax[0].axhline(130, color=C_REF, lw=1.2, ls=":"); ax[0].text(n[0], 133, "5052-H32 Rp0.2 130 MPa", color=C_REF, fontsize=12)
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("elements (tet10, whole model)"); ax[0].set_ylabel("max von Mises [MPa]")
    ax[0].set_title("red: raw nodal peak; blue: design reading; green: yoke bend roots", fontsize=14, loc="left")
    ax[1].plot(n, [m["reader_cg_disp_mag_mm"] for m in L], marker="o", color=C_DES, lw=2.4)
    ax[1].set_xscale("log"); ax[1].set_xlabel("elements (tet10, whole model)"); ax[1].set_ylabel("displacement of reader CG [mm]")
    ax[1].set_title("Reader-CG displacement", fontsize=14, loc="left")
    ax[1].set_ylim(bottom=0)
    fig.suptitle(f"CASE B  antenna tilt bracket - {title}", fontsize=17, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94)); finish(fig, f"convergence_B_bracket_{supp}.png")

# ------------------------------------------------------------------ C
Cs = {}
for tag, m in load("C_boom_*_s*"):
    Cs.setdefault(m["mode"], []).append(m)
if Cs:
    fig, ax = plt.subplots(1, 2, figsize=(16, 6.2))
    for mode, ls in (("vert", "-"), ("horiz", "--")):
        L = sorted(Cs.get(mode, []), key=lambda m: m["shell_elements"])
        if not L: continue
        n = [m["shell_elements"] for m in L]
        ax[0].plot(n, [m["raw_max"] for m in L], marker="o", mfc="white", color=C_RAW, ls=ls, lw=2)
        ax[0].plot(n, [m["max_vm_beyond_XC_plus_60"] for m in L], marker="o", color=C_DES, ls=ls, lw=2.4)
        ax[0].plot(n, [m["beam_sigma_at_XC_MPa"] for m in L], color=C_REF, ls=ls, lw=1.2)
        ax[1].plot(n, [m["tip_disp_FE_mm"] for m in L], marker="o", color=C_DES, ls=ls, lw=2.4)
        ax[1].plot(n, [m["tip_disp_beam_clamped_at_XC_mm"] for m in L], color=C_REF, ls=ls, lw=1.2)
    ax[0].set_xscale("log"); ax[0].set_xlabel("shell elements (S8)"); ax[0].set_ylabel("max von Mises [MPa]")
    ax[0].set_title("red: clamp-end corner peak (mesh-dependent); blue: beyond clamp+60 mm;\ngrey: beam theory at clamp edge (solid vertical, dashed horizontal)", fontsize=14, loc="left")
    ax[1].set_xscale("log"); ax[1].set_xlabel("shell elements (S8)"); ax[1].set_ylabel("tip displacement [mm]")
    ax[1].set_title("blue FE, grey beam theory (clamped at x = 205 mm); solid vertical, dashed horizontal", fontsize=14, loc="left")
    ax[1].set_ylim(bottom=0)
    fig.suptitle("CASE C  barrier boom, 50 N tip load (boom 60x30x1.5 Al 6063-T5, shell model)", fontsize=17, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94)); finish(fig, "convergence_C_boom.png")

# ------------------------------------------------------------------ summary json
summ = {}
for pat in ("A_*", "B_*", "C_*"):
    for tag, m in load(pat):
        summ[tag] = m
json.dump(summ, open(os.path.join(RES, "summary.json"), "w"), indent=1)
print("runs summarised:", len(summ))
