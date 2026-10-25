"""MOCK NETC ledger.

!! THIS IS A MOCK. It does not talk to NPCI, NETC, IHMCL, any acquirer bank or any network.
!! Real FASTag debits need an NPCI-certified acquirer bank (see docs/RISKS.md).
!! It only imitates the *shape* of an acquirer flow (mapper lookup -> debit -> response)
!! so the Edge Node's store-and-forward and idempotency logic can be exercised.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .store import AckLost, LedgerRejected, LedgerUnavailable


@dataclass
class MockNetcLedger:
    fee_paise: int = 2000                       # flat demo fee, 20.00 INR
    accounts: dict = field(default_factory=dict)  # epc_token -> balance (paise)
    processed: dict = field(default_factory=dict) # event_id -> response (idempotency table)
    postings: list = field(default_factory=list)
    online: bool = True
    drop_next_ack: bool = False                 # fault injection
    is_mock: bool = True                        # explicit marker in every response

    def open_account(self, epc_token: str, balance_paise: int) -> None:
        self.accounts[epc_token] = balance_paise

    def submit(self, event_id: str, event: dict) -> dict:
        if not self.online:
            raise LedgerUnavailable("MOCK ledger offline")
        if event_id in self.processed:                       # idempotent replay
            return {**self.processed[event_id], "duplicate": True}
        resp = self._process(event_id, event)
        self.processed[event_id] = resp
        if self.drop_next_ack:                               # processed, but the caller never hears
            self.drop_next_ack = False
            raise AckLost("MOCK ack lost")
        return {**resp, "duplicate": False}

    def _process(self, event_id: str, ev: dict) -> dict:
        resp = {"mock": True, "event_id": event_id, "status": "RECORDED", "debited_paise": 0}
        if ev.get("type") == "LANE_PASS" and ev.get("decision") == "GRANT":
            tok = ev.get("tag_token")
            if tok is None:
                resp["status"] = "NO_TAG_NO_DEBIT"        # plate-only passes are billed offline by the guard process
            elif tok not in self.accounts:
                raise LedgerRejected("MOCK: unknown account")
            elif self.accounts[tok] < self.fee_paise:
                resp["status"] = "INSUFFICIENT_BALANCE"
            else:
                self.accounts[tok] -= self.fee_paise
                resp["debited_paise"] = self.fee_paise
                resp["status"] = "DEBITED"
        self.postings.append((event_id, resp["status"], resp["debited_paise"]))
        return resp
