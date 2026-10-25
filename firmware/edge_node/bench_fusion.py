"""Measure CPU time of the fusion function on THIS machine.

    host CPU, not target hardware, not an end-to-end latency.

It times fuse() (plate normalisation + SQLite allow-list lookups + decision) over a fixed mix
of inputs against an in-memory allow-list of N random plates. It excludes camera capture,
ANPR inference, UART, RFID read time and the Lane Controller. It says NOTHING about whether
the 300 ms decision-latency TARGET is met: that must be bench-verified on the Raspberry Pi 5
with the real pipeline.
"""
import json
import os
import platform
import random
import statistics
import string
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parkflow_edge.fusion import FusionConfig, PlateObs, TagObs, fuse  # noqa: E402
from parkflow_edge.plate import STATE_CODES  # noqa: E402
from parkflow_edge.store import AllowList  # noqa: E402

N_PLATES = int(os.environ.get("BENCH_PLATES", "5000"))
ITER = int(os.environ.get("BENCH_ITER", "20000"))


def rand_plate(rng):
    st = rng.choice(sorted(STATE_CODES))
    return f"{st}{rng.randint(1, 99):02d}{''.join(rng.choices(string.ascii_uppercase, k=2))}{rng.randint(1, 9999):04d}"


def main():
    rng = random.Random(1234)
    db = AllowList()
    rows = []
    while len(rows) < N_PLATES:
        p = rand_plate(rng)
        if db.by_plate(p):
            continue
        epc = f"E280{rng.getrandbits(80):020X}"
        db.add(p, epc, plate_only_ok=rng.random() < 0.2)
        rows.append((p, epc))
    cfg = FusionConfig()
    cases = []
    for i in range(200):
        p, e = rows[rng.randrange(len(rows))]
        q, e2 = rows[rng.randrange(len(rows))]
        noisy = p.replace("0", "O").lower()
        cases += [
            (TagObs(e, 1000, -50), PlateObs(p, 0.95, 1000)),               # exact match
            (TagObs(e, 1000, -50), PlateObs(noisy, 0.9, 1010)),            # OCR-confused match
            (TagObs(e, 1000, -50), PlateObs(q, 0.95, 1000)),               # mismatch
            (None, PlateObs(rand_plate(rng), 0.95, 1000)),                 # unknown plate (near-plate scan)
            (TagObs(e, 1000, -50), None),                                  # tag only
        ]
    for tag, pl in cases[:500]:
        fuse(tag, pl, db, cfg)                                             # warm-up
    t = []
    n = len(cases)
    for i in range(ITER):
        tag, pl = cases[i % n]
        a = time.perf_counter_ns()
        fuse(tag, pl, db, cfg)
        t.append((time.perf_counter_ns() - a) / 1e6)
    t.sort()
    pct = lambda q: t[min(len(t) - 1, int(q * len(t)))]
    cpu = "unknown"
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip(); break
    except OSError:
        pass
    out = {
        "label": "host CPU, not target hardware, not an end-to-end latency",
        "what_was_timed": "fuse(): plate normalisation + in-memory SQLite allow-list lookups + decision",
        "not_included": ["camera capture", "ANPR inference", "RFID read", "UART/serial", "Lane Controller", "disk-backed DB"],
        "machine": {"cpu": cpu, "logical_cpus": os.cpu_count(), "python": platform.python_version(), "os": platform.platform()},
        "allow_list_size": N_PLATES, "calls": ITER,
        "ms": {"mean": statistics.fmean(t), "median": statistics.median(t), "p95": pct(0.95), "p99": pct(0.99), "max": t[-1]},
        "target_300ms_status": "NOT VERIFIED: the 300 ms decision-latency figure is a TARGET to bench-verify on the Raspberry Pi 5",
    }
    print(json.dumps(out, indent=2))
    if len(sys.argv) > 1:
        json.dump(out, open(sys.argv[1], "w"), indent=2)


if __name__ == "__main__":
    main()
