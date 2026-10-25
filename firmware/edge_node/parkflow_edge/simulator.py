"""Scripted lane-scenario replay. Pure software: a virtual clock drives EdgeNode with the exact
serial lines the Lane Controller would send, plus camera plate reads, and checks the outcome.

    python -m parkflow_edge.simulator [--scenarios FILE] [--out JSON]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Optional

from . import link
from .fusion import FusionConfig, PlateObs
from .netc_mock import MockNetcLedger
from .node import EdgeNode
from .store import AllowList, EventQueue, token

CTRL_CLOCK_OFFSET = 7000      # Pi clock minus controller clock, deliberately non-zero
SALT = b"SIM-SALT"
BASE = 10_000
DEC_RE = re.compile(r"\$DEC,(\d+),([GFD]),(\d+)\*")


def build_world(spec: dict):
    db = AllowList()
    for r in spec["allow_list"]:
        db.add(r["plate"], r.get("epc"), r.get("tid"), r.get("vclass", "CAR"), r.get("plate_only_ok", False), r.get("active", True))
    for b in spec["blacklist"]:
        db.blacklist(b["kind"], b["value"])
    ledger = MockNetcLedger()
    for r in spec["allow_list"]:
        if r.get("epc"):
            ledger.open_account(token(r["epc"].upper(), SALT), 50_000)
    return db, EventQueue(backoff_base_ms=500), ledger


def run_scenario(sc: dict, spec: dict, cfg: Optional[FusionConfig] = None) -> dict:
    db, queue, ledger = build_world(spec)
    node = EdgeNode(db, queue, salt=SALT, cfg=cfg or FusionConfig())
    steps = sorted(sc["steps"], key=lambda s: s["t"])
    end = max(s["t"] for s in steps) + 1500
    replies, log = [], []
    sync_results = []
    i = 0
    for t in range(0, end, 10):
        now = BASE + t
        out = []
        while i < len(steps) and steps[i]["t"] <= t:
            s = steps[i]; i += 1
            if "veh" in s:
                out += node.on_controller_line(link.encode(f"VEH,{s['veh']},{now - CTRL_CLOCK_OFFSET}"), now)
            elif "tag" in s:
                g = s["tag"]
                peak = now + g.get("peak_dt", 0) - CTRL_CLOCK_OFFSET
                out += node.on_controller_line(link.encode(f"TAG,{g['seq']},{g['epc']},{g['rssi']},{peak},{g.get('n_distinct', 1)}"), now)
            elif "notag" in s:
                out += node.on_controller_line(link.encode(f"NOTAG,{s['notag']['seq']}"), now)
            elif "plate" in s:
                node.on_plate_read(PlateObs(s["plate"]["text"], s["plate"]["conf"], now))
            elif "pass" in s:
                node.on_controller_line(link.encode(f"PASS,{s['pass']['seq']}"), now)
            elif "ledger" in s:
                ledger.online = s["ledger"] == "online"
            elif "drop_next_ack" in s:
                ledger.drop_next_ack = True
            elif "sync" in s:
                sync_results.append(queue.sync(ledger.submit, now))
        out += node.poll(now)
        replies += [(t, o) for o in out]
    decs = [(t, DEC_RE.search(o)) for t, o in replies if "$DEC" in o]
    first = decs[0][1] if decs else None
    seq_res = node.decisions.get(1)
    result = {
        "name": sc["name"], "description": sc["description"],
        "decision": seq_res.decision.value if seq_res else None,
        "reason": seq_res.reason.name if seq_res else None,
        "alert": seq_res.alert if seq_res else None,
        "possible_clone": seq_res.possible_clone if seq_res else None,
        "flags": seq_res.flags if seq_res else [],
        "distance": seq_res.distance if seq_res else None,
        "dec_line_sent_at_ms": decs[0][0] if decs else None,
        "dec_count": len(decs),
        "queue": queue.counts(), "sync_results": sync_results,
        "debits_total_paise": sum(p[2] for p in ledger.postings),
        "mock_ledger_postings": len(ledger.postings),
    }
    result["failures"] = check(sc.get("expect", {}), result, ledger, spec)
    result["ok"] = not result["failures"]
    return result


def check(exp: dict, r: dict, ledger: MockNetcLedger, spec: dict) -> list:
    bad = []
    for k in ("decision", "reason", "alert", "possible_clone", "distance"):
        if k in exp and r[k] != exp[k]:
            bad.append(f"{k}: expected {exp[k]!r}, got {r[k]!r}")
    for f in exp.get("flags_include", []):
        if f not in r["flags"]:
            bad.append(f"missing flag {f}")
    if r["dec_count"] != 1:
        bad.append(f"expected exactly one DEC line, got {r['dec_count']}")
    if r["dec_line_sent_at_ms"] is not None and r["dec_line_sent_at_ms"] > 700:
        bad.append("DEC sent later than 700 ms of simulated time (controller waits 1000 ms)")
    if "ledger" in exp:
        e = exp["ledger"]
        if "debits_for_E1" in e:
            deb = [p for p in ledger.postings if p[2] > 0]
            if len(deb) != e["debits_for_E1"]:
                bad.append(f"expected {e['debits_for_E1']} debit(s), got {len(deb)}")
        if "queue_pending" in e and r["queue"]["PENDING"] != e["queue_pending"]:
            bad.append(f"queue pending {r['queue']['PENDING']} != {e['queue_pending']}")
    return bad


def main(argv=None) -> int:
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", default=os.path.join(here, "scenarios", "lane_scenarios.json"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    spec = json.load(open(a.scenarios))
    results = [run_scenario(sc, spec) for sc in spec["scenarios"]]
    print(f"{'scenario':38} {'decision':9} {'reason':22} {'alert':5} result")
    for r in results:
        print(f"{r['name']:38} {str(r['decision']):9} {str(r['reason']):22} {str(r['alert']):5} {'OK' if r['ok'] else 'FAIL ' + '; '.join(r['failures'])}")
    n_ok = sum(r["ok"] for r in results)
    print(f"\n{n_ok}/{len(results)} scenarios matched their scripted expectation (MOCK ledger, simulated clock; not a hardware result)")
    if a.out:
        json.dump({"mock": True, "results": results}, open(a.out, "w"), indent=1)
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
