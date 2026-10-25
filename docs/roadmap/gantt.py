"""Render docs/roadmap/roadmap_timeline.png — ParkFlow 4-month fabrication Gantt."""
import datetime as dt
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

D = dt.date
# (workstream, task, start, end, milestone?)
STREAMS = {
    "Mechanical": "#2f6db5",
    "Electronics": "#d9822b",
    "Firmware / AI": "#3a9e6f",
    "Safety & Test": "#c0392b",
    "Pilot & Stage 3": "#7d5ba6",
}
TASKS = [
    ("Mechanical", "CAD freeze (gantry, boom, enclosure)", D(2026, 11, 2), D(2026, 11, 16)),
    ("Mechanical", "FEA sign-off (wind 1.33 kPa, boom, base)", D(2026, 11, 9), D(2026, 11, 27)),
    ("Mechanical", "Fabricate pole, arms, boom, base plate", D(2026, 12, 1), D(2026, 12, 24)),
    ("Electronics", "KiCad schematic + layout (ERC/DRC clean)", D(2026, 11, 2), D(2026, 11, 23)),
    ("Electronics", "Long-lead orders (RFID, camera, Pi 5, AI HAT+)", D(2026, 11, 3), D(2026, 11, 30)),
    ("Electronics", "PCB fab + assembly", D(2026, 11, 24), D(2026, 12, 11)),
    ("Electronics", "PCB bring-up (rails, RS485, H-bridge, E-stop)", D(2026, 12, 10), D(2026, 12, 31)),
    ("Firmware / AI", "ANPR on recorded Indian plate video", D(2026, 12, 1), D(2027, 1, 8)),
    ("Firmware / AI", "RFID-ANPR fusion + mock NETC ledger", D(2027, 1, 4), D(2027, 1, 29)),
    ("Firmware / AI", "Occupancy nodes + P10 LED guidance", D(2027, 1, 11), D(2027, 1, 29)),
    ("Safety & Test", "Barrier safety tests (beam, current, E-stop)", D(2027, 1, 11), D(2027, 1, 29)),
    ("Safety & Test", "Thermal soak 45 °C + IP65 hose check", D(2027, 1, 18), D(2027, 2, 5)),
    ("Pilot & Stage 3", "Campus gate pilot (with permission)", D(2027, 2, 1), D(2027, 2, 19)),
    ("Pilot & Stage 3", "Measure KPIs + Stage 3 readiness review", D(2027, 2, 15), D(2027, 2, 26)),
]
MILESTONES = [
    (D(2026, 11, 27), "M1 Design freeze"),
    (D(2026, 12, 31), "M2 Hardware alive"),
    (D(2027, 1, 29), "M3 Integrated lane"),
    (D(2027, 2, 26), "M4 Stage 3 ready"),
]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13})
fig, ax = plt.subplots(figsize=(19.2, 9.6), dpi=100)
fig.patch.set_facecolor("#ffffff")
ax.set_facecolor("#ffffff")

n = len(TASKS)
for i, (stream, label, s, e) in enumerate(TASKS):
    y = n - 1 - i
    ax.barh(y, (e - s).days, left=mdates.date2num(s), height=0.62,
            color=STREAMS[stream], edgecolor="white", linewidth=1.5, zorder=3)
ax.set_yticks(range(n))
ax.set_yticklabels([t[1] for t in TASKS][::-1], fontsize=13.5, color="#222")
ax.tick_params(axis="y", length=0, pad=10)

# month bands
months = [D(2026, 11, 1), D(2026, 12, 1), D(2027, 1, 1), D(2027, 2, 1), D(2027, 3, 1)]
names = ["Month 1 · Nov 2026\nDesign freeze & orders", "Month 2 · Dec 2026\nFabricate & bring-up",
         "Month 3 · Jan 2027\nIntegrate & safety-test", "Month 4 · Feb 2027\nPilot & measure"]
for k in range(4):
    a, b = mdates.date2num(months[k]), mdates.date2num(months[k + 1])
    if k % 2 == 0:
        ax.axvspan(a, b, color="#f3f5f8", zorder=0)
    ax.text((a + b) / 2, n + 0.15, names[k], ha="center", va="bottom", fontsize=14,
            fontweight="bold", color="#333", linespacing=1.4)

for d, label in MILESTONES:
    x = mdates.date2num(d)
    ax.plot([x, x], [-0.95, n - 0.45], color="#444", linestyle=(0, (4, 3)), linewidth=1.2, zorder=2)
    ax.plot(x, -0.95, marker="D", markersize=11, color="#111", zorder=5, clip_on=False)
    ha = "right" if d.month == 2 else "center"
    ax.text(x + (0.6 if ha == "right" else 0), -1.55, label, ha=ha, va="top", fontsize=12.5, color="#111", fontweight="bold")

ax.set_xlim(mdates.date2num(D(2026, 11, 1)), mdates.date2num(D(2027, 3, 1)))
ax.set_ylim(-1.0, n + 1.25)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.tick_params(axis="x", labelsize=11.5, colors="#555", pad=34)
ax.grid(axis="x", color="#e2e5ea", linewidth=0.8, zorder=1)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#bbb")

handles = [Patch(color=c, label=k) for k, c in STREAMS.items()]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=5,
          frameon=False, fontsize=13, handlelength=1.4, columnspacing=2.2)
fig.suptitle("ParkFlow Demo Lane: 4-month fabrication plan (Nov 2026 to Feb 2027)",
             fontsize=21, fontweight="bold", x=0.02, ha="left", y=0.965, color="#111")
fig.subplots_adjust(left=0.27, right=0.985, top=0.88, bottom=0.2)
out = Path(__file__).with_name("roadmap_timeline.png")
fig.savefig(out, dpi=100, facecolor=fig.get_facecolor())
print(out)
