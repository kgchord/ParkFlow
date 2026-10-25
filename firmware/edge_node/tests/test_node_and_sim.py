import json
import os

import pytest

from parkflow_edge import link, simulator
from parkflow_edge.fusion import PlateObs
from parkflow_edge.node import EdgeNode
from parkflow_edge.store import AllowList, EventQueue

E1 = "E2801160600002055A112233"
SPEC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scenarios", "lane_scenarios.json")


def make():
    db = AllowList(); db.add("MH12AB1234", E1)
    q = EventQueue()
    return EdgeNode(db, q, salt=b"s"), q


def test_link_known_vector_matches_cpp_test_vector():
    assert link.encode("HB,1") == "$HB,1*17\n"          # same literal is parsed by lane_controller/test/test_units.cpp


def test_link_roundtrip_and_rejects():
    m = link.parse(link.encode("TAG,4,E28011,-52,1234,2"))
    assert (m.type, m.seq, m.epc, m.rssi, m.peak_ms, m.n_distinct) == ("TAG", 4, "E28011", -52, 1234, 2)
    assert link.parse(link.encode("TAG,4,E28011,NA,1,1")).rssi is None
    assert link.parse("$HB,1*00\n") is None and link.parse("garbage") is None and link.parse("$X*") is None
    assert link.parse(link.encode("TAG,notanumber")) is None
    st = link.parse(link.encode("ST,IDLE,NONE,3,24000"))
    assert (st.state, st.fault, st.flags, st.v24_mv) == ("IDLE", "NONE", 3, 24000)
    assert link.dec(5, "GRANT", 0) == link.encode("DEC,5,G,0")


def test_node_waits_for_camera_until_deadline_then_answers_once():
    n, q = make()
    out = n.on_controller_line(link.encode("VEH,1,1000"), 5000)
    assert not any("$DEC" in o for o in out)
    out = n.on_controller_line(link.encode(f"TAG,1,{E1},-45,1100,1"), 5100)
    assert not any("$DEC" in o for o in out)                   # no plate yet, deadline not reached
    assert not any("$DEC" in o for o in n.poll(5500))
    out = n.poll(5600)
    decs = [o for o in out if "$DEC" in o]
    assert len(decs) == 1 and decs[0] == link.dec(1, "F", 4)    # TAG_ONLY -> FALLBACK(4)
    assert not any("$DEC" in o for o in n.poll(6000))           # never answered twice
    n.on_controller_line(link.encode(f"TAG,1,{E1},-45,1100,1"), 6100)    # duplicate TAG line
    assert not any("$DEC" in o for o in n.poll(6200))


def test_node_answers_immediately_when_plate_present_and_converts_clock():
    n, q = make()
    n.on_controller_line(link.encode("VEH,1,1000"), 8000)       # controller clock 1000 == node clock 8000
    n.on_plate_read(PlateObs("MH12AB1234", 0.95, 8100))
    out = n.on_controller_line(link.encode(f"TAG,1,{E1},-45,1100,1"), 8100)     # peak 1100 -> node 8100
    assert link.dec(1, "G", 0) in out


def test_node_ignores_garbage_and_unknown_seq():
    n, q = make()
    assert n.on_controller_line("junk", 0) == [] or all("HB" in o for o in n.on_controller_line("junk", 0))
    assert not any("$DEC" in o for o in n.on_controller_line(link.encode(f"TAG,9,{E1},-45,1,1"), 10))


def test_heartbeat_once_per_second():
    n, q = make()
    hbs = [t for t in range(0, 5000, 100) if any("$HB" in o for o in n.poll(t))]
    assert hbs == [0, 1000, 2000, 3000, 4000]


def test_events_carry_tokens_not_plaintext():
    n, q = make()
    n.on_controller_line(link.encode("VEH,1,1000"), 8000)
    n.on_plate_read(PlateObs("MH12AB1234", 0.95, 8100))
    n.on_controller_line(link.encode(f"TAG,1,{E1},-45,1100,1"), 8100)
    n.on_controller_line(link.encode("PASS,1"), 9000)
    rows = [r[0] for r in q.db.execute("SELECT payload FROM events")]
    assert len(rows) == 2
    for r in rows:
        assert "MH12AB1234" not in r and E1 not in r
        assert json.loads(r)["tag_token"] and json.loads(r)["plate_token"]


def test_all_scripted_scenarios_match_expectations():
    spec = json.load(open(SPEC))
    results = [simulator.run_scenario(sc, spec) for sc in spec["scenarios"]]
    bad = [(r["name"], r["failures"]) for r in results if not r["ok"]]
    assert not bad and len(results) == 21
    assert all(r["dec_count"] == 1 for r in results)


def test_simulator_covers_every_mismatch_class():
    spec = json.load(open(SPEC))
    reasons = {simulator.run_scenario(sc, spec)["reason"] for sc in spec["scenarios"]}
    for must in ("MATCH", "TAG_ONLY", "PLATE_ONLY_PASS", "PLATE_ONLY_NO_TAG", "TAG_PLATE_MISMATCH", "SOFT_MATCH", "LOW_CONFIDENCE",
                 "BLACKLIST", "BLACKLIST_NEAR", "UNKNOWN_PLATE", "INACTIVE", "NO_READ", "INVALID_PLATE_FORMAT"):
        assert must in reasons


def test_scripted_expectation_failure_is_detected():
    spec = json.load(open(SPEC))
    sc = dict(next(s for s in spec["scenarios"] if s["name"] == "tag_only"))
    sc["expect"] = {"decision": "GRANT"}
    assert not simulator.run_scenario(sc, spec)["ok"]


def test_cli_returns_zero_and_writes_json(tmp_path):
    out = tmp_path / "r.json"
    assert simulator.main(["--out", str(out)]) == 0
    data = json.load(open(out))
    assert data["mock"] is True and len(data["results"]) == 21
