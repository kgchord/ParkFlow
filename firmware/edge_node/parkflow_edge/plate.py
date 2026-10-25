"""Indian number-plate normalisation.

Handles: spaces/dashes/dots, lower case, the common OCR confusions O/0, I/1, B/8, S/5
(optionally Z/2, G/6), standard state plates and the Bharat (BH) series.

Method: after stripping separators, try every plausible character-class layout of the
right length and, for each, correct characters that sit in a position of the wrong class
(a letter where a digit must be, or vice versa) using the confusion tables. The layout
needing the fewest corrections wins. Ties prefer the most common layout (2 digits RTO,
2 series letters, 4 digits).

NOT verified against the full MoRTH registration rules: the state-code list is a
configurable snapshot and may be incomplete; BH-series letter restrictions are not enforced.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Snapshot of state / UT codes in use (incl. legacy OR/UA, DN merged into DD, TG replaced TS in 2024).
STATE_CODES = frozenset(
    "AN AP AR AS BR CH CG DD DL DN GA GJ HP HR JH JK KA KL LA LD MH ML MN MP MZ NL OD OR PB PY RJ "
    "SK TN TR TS TG UK UA UP WB".split()
)

CORE_DIGIT_TO_LETTER = {"0": "O", "1": "I", "8": "B", "5": "S"}
CORE_LETTER_TO_DIGIT = {v: k for k, v in CORE_DIGIT_TO_LETTER.items()}
EXT_DIGIT_TO_LETTER = {**CORE_DIGIT_TO_LETTER, "2": "Z", "6": "G"}
EXT_LETTER_TO_DIGIT = {v: k for k, v in EXT_DIGIT_TO_LETTER.items()}

_SEP = re.compile(r"[^A-Za-z0-9]")


@dataclass(frozen=True)
class PlateNorm:
    raw: str
    cleaned: str                     # upper-case alphanumerics only, before OCR correction
    canonical: str                   # after correction; compact, e.g. MH12AB1234
    display: str                     # human form, e.g. MH 12 AB 1234
    fmt: str                         # STANDARD | BH | UNPARSED
    corrections: tuple = ()          # ((index, from, to), ...)
    state_ok: bool = False           # STANDARD only: state code in STATE_CODES
    valid: bool = False              # parsed into a known layout (and state known for STANDARD)

    @property
    def n_corrections(self) -> int:
        return len(self.corrections)


def clean(raw: str) -> str:
    return _SEP.sub("", raw or "").upper()


def _fix(ch: str, want: str, extended: bool):
    """Return corrected char for class `want` ('L' letter / 'D' digit) or None if impossible."""
    if want == "L":
        if ch.isalpha():
            return ch
        return (EXT_DIGIT_TO_LETTER if extended else CORE_DIGIT_TO_LETTER).get(ch)
    if ch.isdigit():
        return ch
    return (EXT_LETTER_TO_DIGIT if extended else CORE_LETTER_TO_DIGIT).get(ch)


def _try_layout(s: str, classes: str, extended: bool):
    out, corr = [], []
    for i, (ch, want) in enumerate(zip(s, classes)):
        fixed = _fix(ch, want, extended)
        if fixed is None:
            return None
        if fixed != ch:
            corr.append((i, ch, fixed))
        out.append(fixed)
    return "".join(out), tuple(corr)


def _layouts(n: int):
    """Yield (class string, fmt, preference rank) for a cleaned length n."""
    for d1 in (2, 1):
        for letters in (2, 1, 3):
            for d2 in (4, 3, 2, 1):
                if 2 + d1 + letters + d2 == n:
                    rank = (d1 != 2) * 4 + (letters != 2) * 2 + (d2 != 4) * 1
                    yield "LL" + "D" * d1 + "L" * letters + "D" * d2, "STANDARD", rank
    for letters in (2, 1):  # BH: YY BH #### XX
        if 2 + 2 + 4 + letters == n:
            yield "DDLL" + "DDDD" + "L" * letters, "BH", 8 if letters == 1 else 0


def _display(canon: str, fmt: str, classes: str) -> str:
    if fmt == "BH":
        return f"{canon[:2]} {canon[2:4]} {canon[4:8]} {canon[8:]}"
    # split by class runs: LL | D+ | L+ | D+
    parts, i = [], 0
    while i < len(classes):
        j = i
        while j < len(classes) and classes[j] == classes[i]:
            j += 1
        parts.append(canon[i:j])
        i = j
    return " ".join(parts)


def normalise_plate(raw: str, *, extended_ocr: bool = False) -> PlateNorm:
    s = clean(raw)
    best = None
    for classes, fmt, rank in _layouts(len(s)):
        got = _try_layout(s, classes, extended_ocr)
        if got is None:
            continue
        canon, corr = got
        if fmt == "BH" and canon[2:4] != "BH":
            continue
        if fmt == "STANDARD" and len(s) >= 2 and canon[:2] not in STATE_CODES:
            state_pen = 1
        else:
            state_pen = 0
        key = (state_pen, len(corr), rank)
        if best is None or key < best[0]:
            best = (key, canon, corr, classes, fmt)
    if best is None:
        return PlateNorm(raw=raw, cleaned=s, canonical=s, display=s, fmt="UNPARSED")
    _, canon, corr, classes, fmt = best
    state_ok = fmt == "BH" or canon[:2] in STATE_CODES
    return PlateNorm(raw=raw, cleaned=s, canonical=canon, display=_display(canon, fmt, classes), fmt=fmt,
                     corrections=corr, state_ok=state_ok, valid=state_ok)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
