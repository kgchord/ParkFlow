"""RFID tag <-> plate fusion.

Design rules (from docs/safety/SAFETY.md FMEA #1-#3 and docs/RISKS.md R2):
  * Two-signal rule: automatic GRANT needs the EPC *and* the plate of THIS lane to agree.
  * A tag is used only if this lane's camera has a plate within +-window_ms of the tag's
    peak-RSSI time (adjacent-lane mitigation); otherwise the tag is ignored.
  * Edit distance 1 with the tag matching is a "soft match" -> guard, not auto-open.
  * Tag/plate disagreement is a possible cloned tag -> guard alert, never auto-open.
  * Nothing here hard-blocks a vehicle: DENY is used only for blacklist hits and the
    controller treats DENY exactly like FALLBACK (guard review). 
All thresholds are DESIGN DEFAULTS, not tuned values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .plate import PlateNorm, levenshtein, normalise_plate


class Decision(str, Enum):
    GRANT = "GRANT"
    FALLBACK = "FALLBACK"   # guard review / soft confirm
    DENY = "DENY"           # blacklist only


class Reason(int, Enum):
    MATCH = 0
    PLATE_ONLY_PASS = 1
    SOFT_MATCH = 2
    TAG_PLATE_MISMATCH = 3
    TAG_ONLY = 4
    PLATE_ONLY_NO_TAG = 5
    LOW_CONFIDENCE = 6
    BLACKLIST = 7
    BLACKLIST_NEAR = 8
    TID_MISMATCH = 9
    UNKNOWN_TAG = 10
    UNKNOWN_PLATE = 11
    NO_READ = 12
    INACTIVE = 13
    INVALID_PLATE_FORMAT = 15


@dataclass
class TagObs:
    epc: str                       # upper-case hex
    ts_ms: int                     # peak-RSSI time on the Edge Node clock
    rssi: Optional[float] = None
    tid: Optional[str] = None      # Gen2 TID if the reader returned it
    n_distinct: int = 1


@dataclass
class PlateObs:
    text: str
    conf: float                    # 0..1 from the OCR model
    ts_ms: int


@dataclass
class FusionConfig:
    conf_plate_only: float = 0.80
    conf_fused_min: float = 0.50
    window_ms: int = 500
    rssi_min: Optional[float] = None          # unit follows the reader; disabled by default
    soft_distance: int = 1
    soft_match_grant: bool = False
    allow_tag_only: bool = False
    blacklist_near_distance: int = 1
    extended_ocr: bool = False
    plate_candidate_distance: int = 1


@dataclass
class FusionResult:
    decision: Decision
    reason: Reason
    alert: bool = False                       # guard should look at this one
    possible_clone: bool = False
    flags: list = field(default_factory=list)
    epc: Optional[str] = None
    plate: Optional[str] = None               # canonical plate used
    plate_conf: Optional[float] = None
    distance: Optional[int] = None
    tid_checked: bool = False
    detail: str = ""


def _res(decision, reason, **kw) -> FusionResult:
    return FusionResult(decision, reason, **kw)


def fuse(tag: Optional[TagObs], plate: Optional[PlateObs], db, cfg: FusionConfig = FusionConfig()) -> FusionResult:
    """`db` needs: by_epc(epc)->Rec|None, by_plate(canon)->Rec|None, near_plates(canon, d)->[Rec],
    blacklisted(kind, value)->bool, blacklist_near(canon, d)->bool."""
    flags: list = []
    pn: Optional[PlateNorm] = None
    if plate is not None and plate.text and plate.text.strip():
        pn = normalise_plate(plate.text, extended_ocr=cfg.extended_ocr)
        if pn.n_corrections:
            flags.append(f"OCR_CORRECTED:{pn.n_corrections}")
    plate_ok = pn is not None and len(pn.cleaned) > 0

    # ---- tag gating -------------------------------------------------------------
    if tag is not None:
        if tag.n_distinct > 1:
            flags.append("MULTI_TAG_IN_FIELD")
        if cfg.rssi_min is not None and tag.rssi is not None and tag.rssi < cfg.rssi_min:
            flags.append("WEAK_TAG_IGNORED")
            tag = None
        elif plate_ok and abs(tag.ts_ms - plate.ts_ms) > cfg.window_ms:
            flags.append("CROSS_LANE_TAG_IGNORED")
            tag = None

    epc = tag.epc if tag else None
    canon = pn.canonical if plate_ok else None
    conf = plate.conf if plate_ok else None
    base = dict(flags=flags, epc=epc, plate=canon, plate_conf=conf)

    # ---- blacklist (highest priority) ----------------------------------------------
    if epc and db.blacklisted("EPC", epc):
        return _res(Decision.DENY, Reason.BLACKLIST, alert=True, detail="EPC on blacklist", **base)
    if canon and db.blacklisted("PLATE", canon):
        return _res(Decision.DENY, Reason.BLACKLIST, alert=True, detail="plate on blacklist", **base)
    if canon and pn.valid and db.blacklist_near(canon, cfg.blacklist_near_distance):
        return _res(Decision.FALLBACK, Reason.BLACKLIST_NEAR, alert=True, detail="plate within edit distance of a blacklisted plate", **base)

    # ---- tag + plate -------------------------------------------------------------------
    if tag is not None and plate_ok:
        rec = db.by_epc(epc)
        if rec is None:
            known = db.by_plate(canon)
            d = "plate is registered under a different tag" if known else "tag not in allow-list"
            return _res(Decision.FALLBACK, Reason.UNKNOWN_TAG, detail=d, **base)
        if not rec.active:
            return _res(Decision.FALLBACK, Reason.INACTIVE, **base)
        tid_checked = bool(rec.tid and tag.tid)
        if tid_checked and rec.tid.upper() != tag.tid.upper():
            return _res(Decision.FALLBACK, Reason.TID_MISMATCH, alert=True, possible_clone=True, tid_checked=True,
                        detail="Gen2 TID differs from the one registered for this EPC", **base)
        if conf < cfg.conf_fused_min:
            return _res(Decision.FALLBACK, Reason.LOW_CONFIDENCE, tid_checked=tid_checked, **base)
        dist = levenshtein(canon, rec.plate)
        base["flags"] = flags
        if dist == 0:
            return _res(Decision.GRANT, Reason.MATCH, distance=0, tid_checked=tid_checked, **base)
        if dist <= cfg.soft_distance:
            if cfg.soft_match_grant and conf >= cfg.conf_plate_only:
                return _res(Decision.GRANT, Reason.SOFT_MATCH, distance=dist, tid_checked=tid_checked, **base)
            return _res(Decision.FALLBACK, Reason.SOFT_MATCH, distance=dist, tid_checked=tid_checked,
                        detail="tag matches, plate differs by one character", **base)
        if conf < cfg.conf_plate_only:
            return _res(Decision.FALLBACK, Reason.LOW_CONFIDENCE, distance=dist, tid_checked=tid_checked,
                        detail="plate disagrees with tag but OCR confidence is low: more likely a misread", **base)
        return _res(Decision.FALLBACK, Reason.TAG_PLATE_MISMATCH, alert=True, possible_clone=True, distance=dist,
                    tid_checked=tid_checked, detail="confident plate disagrees with tag record: possible cloned tag", **base)

    # ---- tag only -------------------------------------------------------------------------
    if tag is not None:
        rec = db.by_epc(epc)
        if rec is None:
            return _res(Decision.FALLBACK, Reason.UNKNOWN_TAG, **base)
        if not rec.active:
            return _res(Decision.FALLBACK, Reason.INACTIVE, **base)
        if cfg.allow_tag_only:
            return _res(Decision.GRANT, Reason.TAG_ONLY, **base)
        return _res(Decision.FALLBACK, Reason.TAG_ONLY, detail="no plate seen in window: guard soft-confirm", **base)

    # ---- plate only ------------------------------------------------------------------------
    if plate_ok:
        if conf < cfg.conf_plate_only:
            return _res(Decision.FALLBACK, Reason.LOW_CONFIDENCE, **base)
        if not pn.valid:
            return _res(Decision.FALLBACK, Reason.INVALID_PLATE_FORMAT, detail=f"cannot parse '{pn.cleaned}'", **base)
        rec = db.by_plate(canon)
        if rec is not None:
            if not rec.active:
                return _res(Decision.FALLBACK, Reason.INACTIVE, distance=0, **base)
            if rec.plate_only_ok:
                return _res(Decision.GRANT, Reason.PLATE_ONLY_PASS, distance=0, **base)
            return _res(Decision.FALLBACK, Reason.PLATE_ONLY_NO_TAG, distance=0,
                        detail="registered with a tag but none read", **base)
        near = db.near_plates(canon, cfg.plate_candidate_distance)
        if near:
            return _res(Decision.FALLBACK, Reason.SOFT_MATCH, distance=1, detail="plate one edit from a registered plate", **base)
        return _res(Decision.FALLBACK, Reason.UNKNOWN_PLATE, **base)

    return _res(Decision.FALLBACK, Reason.NO_READ, **base)
