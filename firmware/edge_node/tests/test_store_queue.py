import json

import pytest

from parkflow_edge.netc_mock import MockNetcLedger
from parkflow_edge.store import AckLost, AllowList, EventQueue, LedgerRejected, LedgerUnavailable, token


def test_allowlist_normalises_and_looks_up():
    d = AllowList()
    assert d.add("mh-12-ab-1234", "e2801160600002055a112233") == "MH12AB1234"
    assert d.by_epc("E2801160600002055A112233").plate == "MH12AB1234"
    assert d.by_plate("MH12AB1234").epc == "E2801160600002055A112233"
    assert d.by_epc("nope") is None and d.count() == 1


def test_allowlist_rejects_unparseable_plates():
    with pytest.raises(ValueError):
        AllowList().add("HELLO")


def test_near_plates_and_blacklist_near():
    d = AllowList()
    d.add("MH12AB1234", "E1")
    d.add("MH12AB1299", "E2")
    assert [r.plate for r in d.near_plates("MH12AB1235", 1)] == ["MH12AB1234"]
    assert d.near_plates("MH12AB1234", 1) == []          # exact match is not "near"
    d.blacklist("PLATE", "KA 01 AA 0001")
    assert d.blacklisted("PLATE", "KA01AA0001") and d.blacklist_near("KA01AA0002", 1) and not d.blacklist_near("KA01AA0001", 1)


def test_allowlist_persists_on_disk(tmp_path):
    p = str(tmp_path / "allow.db")
    AllowList(p).add("MH12AB1234", "E1")
    assert AllowList(p).by_epc("E1").plate == "MH12AB1234"


def test_enqueue_is_idempotent_and_survives_reopen(tmp_path):
    p = str(tmp_path / "q.db")
    q = EventQueue(p)
    eid = EventQueue.make_event_id("L1", 1, "PASS", 123)
    assert q.enqueue(eid, {"a": 1}, 0) is True
    assert q.enqueue(eid, {"a": 1}, 5) is False
    assert EventQueue(p).counts()["PENDING"] == 1


def test_event_ids_are_deterministic_and_distinct():
    a = EventQueue.make_event_id("L1", 1, "PASS", 1)
    assert a == EventQueue.make_event_id("L1", 1, "PASS", 1)
    assert len({a, EventQueue.make_event_id("L1", 2, "PASS", 1), EventQueue.make_event_id("L2", 1, "PASS", 1),
                EventQueue.make_event_id("L1", 1, "DECISION", 1)}) == 4


def test_offline_then_sync_preserves_order_and_backs_off():
    q = EventQueue(backoff_base_ms=1000, backoff_cap_ms=4000)
    led = MockNetcLedger()
    for i in range(3):
        q.enqueue(f"e{i}", {"type": "LANE_DECISION", "n": i}, i)
    led.online = False
    r = q.sync(led.submit, now_ms=100)
    assert r == {"sent": 0, "rejected": 0, "stopped_on_error": True}
    assert q.sync(led.submit, now_ms=500)["sent"] == 0                 # inside back-off window: nothing attempted
    led.online = True
    r = q.sync(led.submit, now_ms=1200)
    assert r["sent"] == 3 and q.counts() == {"PENDING": 0, "SENT": 3, "REJECTED": 0}
    assert [p[0] for p in led.postings] == ["e0", "e1", "e2"]


def test_backoff_doubles_and_is_capped():
    q = EventQueue(backoff_base_ms=1000, backoff_cap_ms=4000)
    q.enqueue("e", {}, 0)
    def down(*_): raise LedgerUnavailable("x")
    t = 0
    waits = []
    for _ in range(5):
        q.sync(down, t)
        nxt = q.db.execute("SELECT next_attempt_ms FROM events").fetchone()[0]
        waits.append(nxt - t)
        t = nxt
    assert waits == [1000, 2000, 4000, 4000, 4000]


def test_lost_ack_then_retry_does_not_double_debit():
    q = EventQueue(backoff_base_ms=10)
    led = MockNetcLedger()
    tok = token("E1", b"s")
    led.open_account(tok, 10_000)
    q.enqueue("p1", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": tok}, 0)
    led.drop_next_ack = True
    assert q.sync(led.submit, 0)["stopped_on_error"]
    assert led.accounts[tok] == 8_000                                    # the ledger DID process it
    assert q.counts()["PENDING"] == 1
    assert q.sync(led.submit, 1000)["sent"] == 1                         # retry -> duplicate response
    assert led.accounts[tok] == 8_000 and len(led.postings) == 1
    assert q.sync(led.submit, 5000)["sent"] == 0


def test_permanent_rejection_is_parked_not_retried_forever():
    q = EventQueue()
    led = MockNetcLedger()
    q.enqueue("p", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": "unknown"}, 0)
    assert q.sync(led.submit, 0)["rejected"] == 1
    assert q.counts() == {"PENDING": 0, "SENT": 0, "REJECTED": 1}


def test_mock_ledger_is_labelled_and_idempotent():
    led = MockNetcLedger(fee_paise=500)
    led.open_account("t", 1000)
    r1 = led.submit("x", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": "t"})
    r2 = led.submit("x", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": "t"})
    assert r1["mock"] is True and r2["mock"] is True and not r1["duplicate"] and r2["duplicate"]
    assert led.accounts["t"] == 500
    assert led.submit("y", {"type": "LANE_PASS", "decision": "FALLBACK", "tag_token": "t"})["debited_paise"] == 0
    assert led.submit("z", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": None})["status"] == "NO_TAG_NO_DEBIT"
    led.accounts["t"] = 100
    assert led.submit("w", {"type": "LANE_PASS", "decision": "GRANT", "tag_token": "t"})["status"] == "INSUFFICIENT_BALANCE"
    assert "MOCK" in (__import__("parkflow_edge.netc_mock", fromlist=["x"]).__doc__)


def test_mock_ledger_has_no_network_imports():
    import parkflow_edge.netc_mock as m
    src = open(m.__file__).read()
    for banned in ("import socket", "import requests", "import urllib", "import http", "npci.org"):
        assert banned not in src


def test_tokens_are_salted_stable_and_not_reversible_looking():
    assert token("MH12AB1234", b"a") == token("MH12AB1234", b"a")
    assert token("MH12AB1234", b"a") != token("MH12AB1234", b"b")
    assert "MH12AB1234" not in token("MH12AB1234", b"a") and len(token("x", b"a")) == 32


def test_indexed_near_plates_equals_brute_force():
    import random
    import string
    from parkflow_edge.plate import levenshtein
    rng = random.Random(7)
    d = AllowList()
    plates = set()
    while len(plates) < 300:
        plates.add(f"MH{rng.randint(10, 14)}A{rng.choice('BCD')}{rng.randint(1000, 1099)}")
    for i, p in enumerate(sorted(plates)):
        d.add(p, f"E{i:06d}")
    queries = [rng.choice(sorted(plates)) for _ in range(60)]
    queries += ["".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(10)) for _ in range(20)]
    for _ in range(60):      # mutate: substitute / delete / insert one char
        p = list(rng.choice(sorted(plates)))
        k = rng.randrange(len(p)); op = rng.choice("sdi")
        if op == "s": p[k] = rng.choice(string.digits)
        elif op == "d": del p[k]
        else: p.insert(k, rng.choice(string.digits))
        queries.append("".join(p))
    for q in queries:
        want = sorted(x for x in plates if 0 < levenshtein(q, x) <= 1)
        got = sorted(r.plate for r in d.near_plates(q, 1))
        assert got == want, q
