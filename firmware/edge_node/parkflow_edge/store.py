"""SQLite-backed local allow-list, blacklist and offline event queue.

Privacy note (see docs/FIRMWARE.md): the allow-list holds plaintext plates/EPCs because
edit-distance matching cannot run on HMAC tokens; it is meant to live on the LUKS-encrypted
node disk. EVENTS (queue, ledger) carry only salted HMAC tokens, never plaintext plates/EPCs.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from dataclasses import dataclass
from typing import Callable, Optional

from .plate import levenshtein, normalise_plate


def token(value: str, salt: bytes) -> str:
    """Salted HMAC-SHA256 token (truncated to 32 hex chars) for events leaving the allow-list."""
    return hmac.new(salt, value.encode(), hashlib.sha256).hexdigest()[:32]


@dataclass(frozen=True)
class Rec:
    plate: str
    epc: Optional[str]
    tid: Optional[str]
    vclass: str
    plate_only_ok: bool
    active: bool


def _variants(s: str):
    """The string itself plus every single-character deletion."""
    return {s} | {s[:i] + s[i + 1:] for i in range(len(s))}


class AllowList:
    def __init__(self, path: str = ":memory:", extended_ocr: bool = False):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS vehicles(
              plate TEXT PRIMARY KEY, epc TEXT UNIQUE, tid TEXT, vclass TEXT NOT NULL DEFAULT 'CAR',
              plate_only_ok INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1);
            CREATE INDEX IF NOT EXISTS ix_epc ON vehicles(epc);
            -- deletion-neighbourhood index: any two plates within edit distance 1 share a variant
            CREATE TABLE IF NOT EXISTS del_idx(variant TEXT NOT NULL, plate TEXT NOT NULL, PRIMARY KEY(variant, plate)) WITHOUT ROWID;
            CREATE TABLE IF NOT EXISTS blacklist(
              kind TEXT NOT NULL CHECK(kind IN ('PLATE','EPC')), value TEXT NOT NULL, reason TEXT,
              PRIMARY KEY(kind, value));
            """)
        self.ext = extended_ocr

    # -- maintenance
    def add(self, plate: str, epc: Optional[str] = None, tid: Optional[str] = None, vclass: str = "CAR",
            plate_only_ok: bool = False, active: bool = True) -> str:
        pn = normalise_plate(plate, extended_ocr=self.ext)
        if not pn.valid:
            raise ValueError(f"plate '{plate}' does not parse as a valid Indian plate")
        self.db.execute("INSERT OR REPLACE INTO vehicles VALUES(?,?,?,?,?,?)",
                        (pn.canonical, epc.upper() if epc else None, tid.upper() if tid else None, vclass,
                         int(plate_only_ok), int(active)))
        self.db.executemany("INSERT OR IGNORE INTO del_idx VALUES(?,?)", [(v, pn.canonical) for v in _variants(pn.canonical)])
        self.db.commit()
        return pn.canonical

    def blacklist(self, kind: str, value: str, reason: str = "") -> None:
        v = normalise_plate(value, extended_ocr=self.ext).canonical if kind == "PLATE" else value.upper()
        self.db.execute("INSERT OR REPLACE INTO blacklist VALUES(?,?,?)", (kind, v, reason))
        self.db.commit()

    def count(self) -> int:
        return self.db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]

    # -- lookups used by fusion
    @staticmethod
    def _rec(row) -> Optional[Rec]:
        return Rec(row[0], row[1], row[2], row[3], bool(row[4]), bool(row[5])) if row else None

    def by_epc(self, epc: str) -> Optional[Rec]:
        return self._rec(self.db.execute("SELECT plate,epc,tid,vclass,plate_only_ok,active FROM vehicles WHERE epc=?", (epc.upper(),)).fetchone())

    def by_plate(self, canon: str) -> Optional[Rec]:
        return self._rec(self.db.execute("SELECT plate,epc,tid,vclass,plate_only_ok,active FROM vehicles WHERE plate=?", (canon,)).fetchone())

    def near_plates(self, canon: str, d: int = 1) -> list:
        if d == 1:   # indexed path: O(len) lookups instead of an O(N) edit-distance scan
            vs = list(_variants(canon))
            q = ",".join("?" * len(vs))
            rows = self.db.execute(f"SELECT DISTINCT v.plate,v.epc,v.tid,v.vclass,v.plate_only_ok,v.active FROM del_idx i "
                                   f"JOIN vehicles v ON v.plate=i.plate WHERE i.variant IN ({q})", vs).fetchall()
            return [self._rec(r) for r in rows if 0 < levenshtein(canon, r[0]) <= 1]
        rows = self.db.execute("SELECT plate,epc,tid,vclass,plate_only_ok,active FROM vehicles WHERE ABS(LENGTH(plate)-?)<=?",
                               (len(canon), d)).fetchall()
        return [self._rec(r) for r in rows if 0 < levenshtein(canon, r[0]) <= d]

    def blacklisted(self, kind: str, value: str) -> bool:
        return self.db.execute("SELECT 1 FROM blacklist WHERE kind=? AND value=?", (kind, value)).fetchone() is not None

    def blacklist_near(self, canon: str, d: int = 1) -> bool:
        rows = self.db.execute("SELECT value FROM blacklist WHERE kind='PLATE' AND ABS(LENGTH(value)-?)<=?", (len(canon), d)).fetchall()
        return any(0 < levenshtein(canon, r[0]) <= d for r in rows)


class LedgerUnavailable(Exception):
    """Transient: no connectivity / ledger down. Event stays queued."""


class LedgerRejected(Exception):
    """Permanent: ledger refused the event. Event is parked as REJECTED."""


class AckLost(LedgerUnavailable):
    """Test hook: the ledger processed the event but the acknowledgement never arrived."""


class EventQueue:
    """Store-and-forward queue. event_id is the idempotency key end to end: re-enqueueing the same
    event is a no-op, and the ledger de-duplicates on the same key, so a retry after a lost ack
    cannot double-post."""

    def __init__(self, path: str = ":memory:", backoff_base_ms: int = 1000, backoff_cap_ms: int = 60000):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS events(
               seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'PENDING', attempts INTEGER NOT NULL DEFAULT 0,
               next_attempt_ms INTEGER NOT NULL DEFAULT 0, last_error TEXT, created_ms INTEGER NOT NULL)""")
        self.base, self.cap = backoff_base_ms, backoff_cap_ms

    @staticmethod
    def make_event_id(lane_id: str, veh_seq: int, kind: str, ts_ms: int) -> str:
        return hashlib.sha256(f"{lane_id}|{veh_seq}|{kind}|{ts_ms}".encode()).hexdigest()[:32]

    def enqueue(self, event_id: str, payload: dict, now_ms: int) -> bool:
        cur = self.db.execute("INSERT OR IGNORE INTO events(event_id,payload,created_ms) VALUES(?,?,?)",
                              (event_id, json.dumps(payload, sort_keys=True), now_ms))
        self.db.commit()
        return cur.rowcount == 1

    def counts(self) -> dict:
        d = {"PENDING": 0, "SENT": 0, "REJECTED": 0}
        for s, n in self.db.execute("SELECT status,COUNT(*) FROM events GROUP BY status"):
            d[s] = n
        return d

    def sync(self, submit: Callable[[str, dict], object], now_ms: int, max_batch: int = 100) -> dict:
        """Oldest-first. Stops at the first transient failure (preserves order, applies back-off)."""
        sent = rejected = 0
        head = self.db.execute("SELECT next_attempt_ms FROM events WHERE status='PENDING' ORDER BY seq LIMIT 1").fetchone()
        if head is not None and head[0] > now_ms:       # head-of-line is backing off: do not let younger events overtake it
            return {"sent": 0, "rejected": 0, "stopped_on_error": False}
        rows = self.db.execute("SELECT seq,event_id,payload,attempts FROM events WHERE status='PENDING' AND next_attempt_ms<=? ORDER BY seq LIMIT ?",
                               (now_ms, max_batch)).fetchall()
        stopped = False
        for seq, eid, payload, attempts in rows:
            try:
                submit(eid, json.loads(payload))
            except LedgerRejected as e:
                self.db.execute("UPDATE events SET status='REJECTED',attempts=attempts+1,last_error=? WHERE seq=?", (str(e), seq))
                rejected += 1
            except LedgerUnavailable as e:
                delay = min(self.cap, self.base * (2 ** attempts))
                self.db.execute("UPDATE events SET attempts=attempts+1,next_attempt_ms=?,last_error=? WHERE seq=?",
                                (now_ms + delay, type(e).__name__, seq))
                stopped = True
                self.db.commit()
                break
            else:
                self.db.execute("UPDATE events SET status='SENT',attempts=attempts+1,last_error=NULL WHERE seq=?", (seq,))
                sent += 1
            self.db.commit()
        return {"sent": sent, "rejected": rejected, "stopped_on_error": stopped}
