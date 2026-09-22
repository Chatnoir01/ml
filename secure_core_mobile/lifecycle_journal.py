"""Deterministic lifecycle journal for crash-recovery semantics.

Development implementation is in-memory. Entries describe intent/commit so an
unfinished destructive or rotational transition is detectable after restart.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from threading import Lock
import hashlib
import json
import secrets


class JournalPhase(str, Enum):
    INTENT = "INTENT"
    COMMIT = "COMMIT"


@dataclass(frozen=True)
class JournalEntry:
    txid: str
    operation: str
    handle: str
    phase: JournalPhase
    previous_sha256: str
    entry_sha256: str


class InMemoryLifecycleJournal:
    durable = False

    def __init__(self) -> None:
        self._entries: list[JournalEntry] = []
        self._lock = Lock()

    def _append(self, *, txid: str, operation: str, handle: str, phase: JournalPhase) -> JournalEntry:
        with self._lock:
            previous = self._entries[-1].entry_sha256 if self._entries else "0" * 64
            body = json.dumps({
                "txid": txid, "operation": operation, "handle": handle,
                "phase": phase.value, "previous_sha256": previous,
            }, sort_keys=True, separators=(",", ":")).encode()
            digest = hashlib.sha256(body).hexdigest()
            entry = JournalEntry(txid, operation, handle, phase, previous, digest)
            self._entries.append(entry)
            return entry

    def begin(self, *, operation: str, handle: str) -> str:
        txid = secrets.token_hex(16)
        self._append(txid=txid, operation=operation, handle=handle, phase=JournalPhase.INTENT)
        return txid

    def commit(self, txid: str, *, operation: str, handle: str) -> JournalEntry:
        return self._append(txid=txid, operation=operation, handle=handle, phase=JournalPhase.COMMIT)

    def incomplete(self) -> tuple[JournalEntry, ...]:
        with self._lock:
            committed = {e.txid for e in self._entries if e.phase is JournalPhase.COMMIT}
            return tuple(e for e in self._entries if e.phase is JournalPhase.INTENT and e.txid not in committed)

    def verify_chain(self) -> None:
        previous = "0" * 64
        for entry in self._entries:
            if entry.previous_sha256 != previous:
                raise ValueError("lifecycle journal chain broken")
            body = json.dumps({
                "txid": entry.txid, "operation": entry.operation, "handle": entry.handle,
                "phase": entry.phase.value, "previous_sha256": entry.previous_sha256,
            }, sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(body).hexdigest() != entry.entry_sha256:
                raise ValueError("lifecycle journal entry digest mismatch")
            previous = entry.entry_sha256
