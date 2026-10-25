import pytest

from parkflow_edge.fusion import Decision, FusionConfig, PlateObs, Reason, TagObs, fuse
from parkflow_edge.store import AllowList

E_MH, E_KA, E_DL = "E2801160600002055A112233", "E28011606000020777889900", "E2801160600002061B445566"


@pytest.fixture()
def db():
    d = AllowList()
    d.add("MH12AB1234", E_MH, tid="E2003412013EAA01")
    d.add("KA01MN4567", E_KA)
    d.add("DL3CAB1234", E_DL, active=False)
    d.add("UP32AB1111", None, vclass="TWO_WHEELER", plate_only_ok=True)
    d.blacklist("PLATE", "MH14ZZ9999")
    d.blacklist("EPC", "E28011606000020999999999")
    return d


def T(epc=E_MH, ts=1000, rssi=-45.0, tid=None, n=1): return TagObs(epc, ts, rssi, tid, n)
def P(text="MH12AB1234", conf=0.95, ts=1000): return PlateObs(text, conf, ts)


def test_match_grants(db):
    r = fuse(T(), P(), db)
    assert (r.decision, r.reason, r.distance) == (Decision.GRANT, Reason.MATCH, 0)


def test_ocr_confusions_still_match(db):
    r = fuse(T(), P("mhi2-a8-1234"), db)
    assert r.decision == Decision.GRANT and "OCR_CORRECTED:2" in r.flags


def test_soft_match_goes_to_guard_by_default_and_never_grants_when_tag_unknown(db):
    r = fuse(T(), P("MH12AB1284"), db)
    assert (r.decision, r.reason, r.distance) == (Decision.FALLBACK, Reason.SOFT_MATCH, 1)
    assert not r.possible_clone


def test_soft_match_can_be_policy_enabled_only_with_high_confidence(db):
    cfg = FusionConfig(soft_match_grant=True)
    assert fuse(T(), P("MH12AB1284", 0.9), db, cfg).decision == Decision.GRANT
    assert fuse(T(), P("MH12AB1284", 0.6), db, cfg).decision == Decision.FALLBACK


def test_confident_mismatch_is_possible_clone_with_alert(db):
    r = fuse(T(E_KA), P("MH12AB1234", 0.96), db)
    assert (r.decision, r.reason) == (Decision.FALLBACK, Reason.TAG_PLATE_MISMATCH)
    assert r.alert and r.possible_clone and r.distance >= 2


def test_low_confidence_mismatch_is_not_accused_of_cloning(db):
    r = fuse(T(E_KA), P("MH12AB1234", 0.55), db)
    assert (r.reason, r.possible_clone, r.alert) == (Reason.LOW_CONFIDENCE, False, False)


@pytest.mark.parametrize("conf", [0.0, 0.2, 0.49])
def test_below_fused_min_is_low_confidence_even_if_text_matches(db, conf):
    assert fuse(T(), P(conf=conf), db).reason == Reason.LOW_CONFIDENCE


def test_tid_mismatch_is_clone_even_when_plate_matches(db):
    r = fuse(T(tid="E2003412013EBB02"), P(), db)
    assert (r.decision, r.reason, r.possible_clone, r.tid_checked) == (Decision.FALLBACK, Reason.TID_MISMATCH, True, True)


def test_tid_match_is_recorded_and_grants(db):
    r = fuse(T(tid="e2003412013eaa01"), P(), db)
    assert r.decision == Decision.GRANT and r.tid_checked


def test_tid_not_available_is_visible_as_unchecked(db):
    assert fuse(T(), P(), db).tid_checked is False


def test_tag_only_goes_to_guard_unless_policy_allows(db):
    r = fuse(T(), None, db)
    assert (r.decision, r.reason) == (Decision.FALLBACK, Reason.TAG_ONLY)
    assert fuse(T(), PlateObs("", 0.0, 1000), db).reason == Reason.TAG_ONLY
    assert fuse(T(), None, db, FusionConfig(allow_tag_only=True)).decision == Decision.GRANT


def test_unknown_tag_with_or_without_plate(db):
    assert fuse(T("E280AAAA"), None, db).reason == Reason.UNKNOWN_TAG
    r = fuse(T("E280AAAA"), P("MH12AB1234"), db)
    assert r.reason == Reason.UNKNOWN_TAG and "different tag" in r.detail


def test_inactive_registration(db):
    assert fuse(T(E_DL), P("DL3CAB1234"), db).reason == Reason.INACTIVE
    assert fuse(T(E_DL), None, db).reason == Reason.INACTIVE


def test_plate_only_paths(db):
    assert fuse(None, P("UP32AB1111"), db).reason == Reason.PLATE_ONLY_PASS
    assert fuse(None, P("UP32AB1111"), db).decision == Decision.GRANT
    assert fuse(None, P("MH12AB1234"), db).reason == Reason.PLATE_ONLY_NO_TAG
    assert fuse(None, P("RJ14CD2222"), db).reason == Reason.UNKNOWN_PLATE
    assert fuse(None, P("UP32AB1112"), db).reason == Reason.SOFT_MATCH
    assert fuse(None, P("UP32AB1111", 0.7), db).reason == Reason.LOW_CONFIDENCE      # below plate-only threshold
    assert fuse(None, P("ZZ12AB1234"), db).reason == Reason.INVALID_PLATE_FORMAT


def test_nothing_read(db):
    r = fuse(None, None, db)
    assert (r.decision, r.reason) == (Decision.FALLBACK, Reason.NO_READ)


def test_blacklist_has_priority_and_is_the_only_deny(db):
    assert fuse(None, P("MH14ZZ9999"), db).decision == Decision.DENY
    assert fuse(T("E28011606000020999999999"), P("RJ14CD2222"), db).decision == Decision.DENY
    r = fuse(T(), P("MH14ZZ9998", 0.9), db)           # one edit from blacklisted plate; tag would otherwise mismatch
    assert (r.decision, r.reason, r.alert) == (Decision.FALLBACK, Reason.BLACKLIST_NEAR, True)


def test_time_window_boundary_is_inclusive_at_500ms(db):
    assert fuse(T(ts=1000), P(ts=1500), db).decision == Decision.GRANT
    assert fuse(T(ts=1000), P(ts=500), db).decision == Decision.GRANT
    r = fuse(T(ts=1000), P(ts=1501), db)
    assert "CROSS_LANE_TAG_IGNORED" in r.flags and r.reason == Reason.PLATE_ONLY_NO_TAG and r.epc is None


def test_weak_tag_gate_when_enabled(db):
    cfg = FusionConfig(rssi_min=-60.0)
    r = fuse(T(rssi=-75.0), P(), db, cfg)
    assert "WEAK_TAG_IGNORED" in r.flags and r.reason == Reason.PLATE_ONLY_NO_TAG
    assert fuse(T(rssi=-50.0), P(), db, cfg).decision == Decision.GRANT
    assert fuse(T(rssi=-75.0), P(), db).decision == Decision.GRANT          # disabled by default


def test_multi_tag_in_field_is_flagged_but_still_decides(db):
    r = fuse(T(n=3), P(), db)
    assert r.decision == Decision.GRANT and "MULTI_TAG_IN_FIELD" in r.flags


def test_grant_requires_both_signals_unless_plate_only_pass(db):
    # property: over a grid of inputs, GRANT happens only for MATCH or PLATE_ONLY_PASS
    tags = [None, T(), T(E_KA), T("E280AAAA"), T(E_DL)]
    plates = [None, P(), P("MH12AB1284"), P("KA01MN4567"), P("UP32AB1111"), P("RJ14CD2222"), P(conf=0.3), P("MH14ZZ9999"), P("garbage")]
    n = 0
    for t in tags:
        for p in plates:
            r = fuse(t, p, db)
            n += 1
            if r.decision == Decision.GRANT:
                assert r.reason in (Reason.MATCH, Reason.PLATE_ONLY_PASS)
                if r.reason == Reason.MATCH:
                    assert t is not None and p is not None and r.distance == 0
            if r.decision == Decision.DENY:
                assert r.reason == Reason.BLACKLIST
    assert n == 45
