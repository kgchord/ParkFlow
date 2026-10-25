"""Edge Node side of the Lane Controller serial protocol (mirror of lane_controller/include/edge_link.h).

    $TYPE,arg,arg*HH\\n      HH = XOR of the bytes between '$' and '*', two upper-case hex digits
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


def checksum(body: str) -> int:
    c = 0
    for ch in body.encode():
        c ^= ch
    return c


def encode(body: str) -> str:
    return f"${body}*{checksum(body):02X}\n"


def hb(n: int) -> str: return encode(f"HB,{n}")
def dec(seq: int, d: str, reason: int = 0) -> str: return encode(f"DEC,{seq},{d[0]},{reason}")
def guard() -> str: return encode("GUARD")
def rearm() -> str: return encode("REARM")
def reset() -> str: return encode("RESET")


@dataclass
class CtrlMsg:
    type: str
    seq: int = 0
    t_ms: int = 0
    epc: Optional[str] = None
    rssi: Optional[int] = None
    peak_ms: int = 0
    n_distinct: int = 0
    state: str = ""
    fault: str = ""
    flags: int = 0
    v24_mv: int = 0


def parse(line: str) -> Optional[CtrlMsg]:
    """Returns None for anything malformed or with a bad checksum."""
    line = line.strip()
    if not line.startswith("$") or len(line) < 5 or line[-3] != "*":
        return None
    body, ck = line[1:-3], line[-2:]
    try:
        if int(ck, 16) != checksum(body):
            return None
        t, *a = body.split(",")
        if t == "VEH": return CtrlMsg("VEH", seq=int(a[0]), t_ms=int(a[1]))
        if t == "TAG":
            return CtrlMsg("TAG", seq=int(a[0]), epc=a[1].upper(), rssi=None if a[2] == "NA" else int(a[2]),
                           peak_ms=int(a[3]), n_distinct=int(a[4]))
        if t in ("NOTAG", "PASS", "REV"): return CtrlMsg(t, seq=int(a[0]))
        if t == "ST": return CtrlMsg("ST", state=a[0], fault=a[1], flags=int(a[2]), v24_mv=int(a[3]))
    except (ValueError, IndexError):
        return None
    return None
