import pytest

from parkflow_edge.plate import levenshtein, normalise_plate


@pytest.mark.parametrize("raw", ["MH12AB1234", "mh 12 ab 1234", "MH-12-AB-1234", "MH.12.AB.1234", "  MH 12  AB1234 ", "Mh_12/aB 1234"])
def test_separators_and_case_are_ignored(raw):
    p = normalise_plate(raw)
    assert p.canonical == "MH12AB1234" and p.display == "MH 12 AB 1234"
    assert p.fmt == "STANDARD" and p.valid and p.n_corrections == 0


@pytest.mark.parametrize("raw,canon", [
    ("MH12AB123O", "MH12AB1230"),      # O in a digit position
    ("MHI2AB1234", "MH12AB1234"),      # I in a digit position
    ("MH12A81234", "MH12AB1234"),      # 8 in a letter position
    ("MH12AB12S4", "MH12AB1254"),      # S in a digit position
    ("MH125B1234", "MH12SB1234"),      # 5 in a letter position
])
def test_core_ocr_confusions(raw, canon):
    p = normalise_plate(raw)
    assert p.canonical == canon and p.valid and p.n_corrections == 1


def test_confused_state_code_is_flagged_not_silently_accepted():
    p = normalise_plate("0L3CAB1234")      # 0 for D? 'OL' is not a state code
    assert p.fmt == "STANDARD" and not p.valid


@pytest.mark.parametrize("raw,canon,disp", [
    ("DL3CAB1234", "DL3CAB1234", "DL 3 CAB 1234"),
    ("DL-3C-AB-1234", "DL3CAB1234", "DL 3 CAB 1234"),
    ("KA01MN4567", "KA01MN4567", "KA 01 MN 4567"),
    ("MH12A1234", "MH12A1234", "MH 12 A 1234"),
    ("TG09AB0001", "TG09AB0001", "TG 09 AB 0001"),
])
def test_standard_layouts(raw, canon, disp):
    p = normalise_plate(raw)
    assert (p.canonical, p.display, p.fmt, p.valid) == (canon, disp, "STANDARD", True)


@pytest.mark.parametrize("raw,canon,corr", [
    ("22BH1234AA", "22BH1234AA", 0),
    ("22 BH 1234 AA", "22BH1234AA", 0),
    ("22-bh-1234-a", "22BH1234A", 0),
    ("228H1234AA", "22BH1234AA", 1),    # 8 for B
    ("2285 1234AA".replace(" ", ""), None, None),
])
def test_bh_series(raw, canon, corr):
    p = normalise_plate(raw)
    if canon is None:
        assert p.fmt != "BH"
        return
    assert p.fmt == "BH" and p.canonical == canon and p.n_corrections == corr and p.valid
    assert p.display.startswith(canon[:2] + " BH ")


def test_bh_display():
    assert normalise_plate("22bh1234aa").display == "22 BH 1234 AA"


def test_unknown_state_is_parsed_but_not_valid():
    p = normalise_plate("ZZ12AB1234")
    assert p.fmt == "STANDARD" and not p.state_ok and not p.valid


@pytest.mark.parametrize("raw", ["", "   ", "HELLO", "M#1 2 A", "12345678901234", "A"])
def test_garbage_is_unparsed(raw):
    p = normalise_plate(raw)
    assert p.fmt == "UNPARSED" and not p.valid


def test_zero_corrections_preferred_over_clever_rewrites():
    # 'MH1ZAB1234' is a legal 1-digit-RTO / 3-letter-series reading; it must not be "corrected" to MH12AB1234
    assert normalise_plate("MH1ZAB1234").canonical == "MH1ZAB1234"
    # with the optional Z/2 confusion enabled a 2-layout tie still prefers the zero-correction reading
    assert normalise_plate("MH1ZAB1234", extended_ocr=True).canonical == "MH1ZAB1234"


def test_extended_confusions_are_opt_in():
    assert normalise_plate("MH12AB12G4", extended_ocr=True).canonical == "MH12AB1264"
    assert not normalise_plate("MH12AB12G4").valid


def test_ocr_variants_collapse_to_same_canonical():
    variants = ["MH12AB1234", "MHI2AB1234", "MH12A81234", "mh-12-ab-1234"]
    assert len({normalise_plate(v).canonical for v in variants}) == 1


@pytest.mark.parametrize("a,b,d", [("kitten", "sitting", 3), ("", "abc", 3), ("abc", "abc", 0), ("MH12AB1234", "MH12AB1284", 1),
                                   ("abc", "", 3), ("flaw", "lawn", 2)])
def test_levenshtein(a, b, d):
    assert levenshtein(a, b) == d == levenshtein(b, a)
