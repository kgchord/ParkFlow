"""Edge Node orchestration: controller lines + camera plate reads -> fusion -> DEC reply + queued events."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import link
from .fusion import Decision, FusionConfig, FusionResult, PlateObs, TagObs, fuse
from .store import AllowList, EventQueue, token


@dataclass
class _Pending:
    seq: int
    veh_pi_ms: int
    offset_ms: int                   # pi_clock - controller_clock, estimated at VEH
    tag_msg_seen: bool = False
    tag: Optional[TagObs] = None
    answered: bool = False
    deadline_ms: int = 0
    result: Optional[FusionResult] = None


class EdgeNode:
    def __init__(self, db: AllowList, queue: EventQueue, *, lane_id: str = "LANE1", salt: bytes = b"DEMO-SALT-CHANGE-ME",
                 cfg: FusionConfig = FusionConfig(), decision_deadline_ms: int = 600):
        self.db, self.q, self.lane, self.salt, self.cfg = db, queue, lane_id, salt, cfg
        self.deadline = decision_deadline_ms   # must stay < controller decision_timeout_ms (1000)
        self.pending: dict[int, _Pending] = {}
        self.plates: list[PlateObs] = []
        self.hb_n = 0
        self.next_hb = 0
        self.decisions: dict[int, FusionResult] = {}
        self.ctrl_state = ""

    # ---- inputs ------------------------------------------------------------------
    def on_plate_read(self, p: PlateObs) -> None:
        self.plates.append(p)
        self.plates = self.plates[-16:]

    def on_controller_line(self, line: str, now_ms: int) -> list:
        m = link.parse(line)
        if m is None:
            return []
        if m.type == "VEH":
            self.pending[m.seq] = _Pending(m.seq, now_ms, now_ms - m.t_ms, deadline_ms=now_ms + self.deadline)
        elif m.type == "TAG" and m.seq in self.pending:
            p = self.pending[m.seq]
            p.tag_msg_seen = True
            p.tag = TagObs(epc=m.epc, ts_ms=m.peak_ms + p.offset_ms, rssi=m.rssi, n_distinct=m.n_distinct)
        elif m.type == "NOTAG" and m.seq in self.pending:
            self.pending[m.seq].tag_msg_seen = True
        elif m.type == "PASS":
            self._queue_pass(m.seq, now_ms)
        elif m.type == "ST":
            self.ctrl_state = m.state
        return self.poll(now_ms)

    # ---- periodic ------------------------------------------------------------------------
    def poll(self, now_ms: int) -> list:
        out = []
        if now_ms >= self.next_hb:
            self.hb_n += 1
            out.append(link.hb(self.hb_n))
            self.next_hb = now_ms + 1000
        for seq, p in list(self.pending.items()):
            if p.answered or not p.tag_msg_seen:
                continue
            plate = self._pick_plate(p)
            if plate is None and now_ms < p.deadline_ms:
                continue                              # camera may still deliver
            res = fuse(p.tag, plate, self.db, self.cfg)
            p.answered, p.result = True, res
            self.decisions[seq] = res
            code = {"GRANT": "G", "FALLBACK": "F", "DENY": "D"}[res.decision.value]
            out.append(link.dec(seq, code, int(res.reason)))
            self._queue_decision(p, res, now_ms)
        return out

    def _pick_plate(self, p: _Pending) -> Optional[PlateObs]:
        lo = p.veh_pi_ms - self.cfg.window_ms
        c = [x for x in self.plates if x.ts_ms >= lo]
        return max(c, key=lambda x: x.conf) if c else None

    # ---- events (tokens only) ------------------------------------------------------------
    def _tok(self, v: Optional[str]) -> Optional[str]:
        return token(v, self.salt) if v else None

    def _queue_decision(self, p: _Pending, res: FusionResult, now_ms: int) -> None:
        eid = EventQueue.make_event_id(self.lane, p.seq, "DECISION", p.veh_pi_ms)
        self.q.enqueue(eid, {"type": "LANE_DECISION", "lane": self.lane, "seq": p.seq, "decision": res.decision.value,
                             "reason": res.reason.name, "alert": res.alert, "possible_clone": res.possible_clone,
                             "flags": res.flags, "tag_token": self._tok(res.epc), "plate_token": self._tok(res.plate),
                             "ts_ms": p.veh_pi_ms}, now_ms)

    def _queue_pass(self, seq: int, now_ms: int) -> None:
        res = self.decisions.get(seq)
        if res is None:
            return
        eid = EventQueue.make_event_id(self.lane, seq, "PASS", self.pending[seq].veh_pi_ms if seq in self.pending else 0)
        self.q.enqueue(eid, {"type": "LANE_PASS", "lane": self.lane, "seq": seq, "decision": res.decision.value,
                             "reason": res.reason.name, "tag_token": self._tok(res.epc),
                             "plate_token": self._tok(res.plate), "ts_ms": now_ms}, now_ms)

    def guard_open(self) -> str:
        return link.guard()
