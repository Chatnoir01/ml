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
        with self._lock:
            intents = [e for e in self._entries if e.txid == txid and e.phase is JournalPhase.INTENT]
            commits = [e for e in self._entries if e.txid == txid and e.phase is JournalPhase.COMMIT]
            if len(intents) != 1:
                raise ValueError("lifecycle journal commit requires exactly one matching intent")
            intent = intents[0]
            if intent.operation != operation or intent.handle != handle:
                raise ValueError("lifecycle journal commit metadata mismatch")
            if commits:
                raise ValueError("lifecycle journal transaction already committed")
            previous = self._entries[-1].entry_sha256 if self._entries else "0" * 64
            body = json.dumps({
                "txid": txid, "operation": operation, "handle": handle,
                "phase": JournalPhase.COMMIT.value, "previous_sha256": previous,
            }, sort_keys=True, separators=(",", ":")).encode()
            digest = hashlib.sha256(body).hexdigest()
            entry = JournalEntry(txid, operation, handle, JournalPhase.COMMIT, previous, digest)
            self._entries.append(entry)
            return entry

    def incomplete(self) -> tuple[JournalEntry, ...]:
        with self._lock:
            committed = {
                (e.txid, e.operation, e.handle)
                for e in self._entries if e.phase is JournalPhase.COMMIT
            }
            return tuple(
                e for e in self._entries
                if e.phase is JournalPhase.INTENT
                and (e.txid, e.operation, e.handle) not in committed
            )

    def verify_chain(self) -> None:
        with self._lock:
            entries = tuple(self._entries)
        previous = "0" * 64
        seen_intents: dict[str, tuple[str, str]] = {}
        committed: set[str] = set()
        for entry in entries:
            if entry.previous_sha256 != previous:
                raise ValueError("lifecycle journal chain broken")
            body = json.dumps({
                "txid": entry.txid, "operation": entry.operation, "handle": entry.handle,
                "phase": entry.phase.value, "previous_sha256": entry.previous_sha256,
            }, sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(body).hexdigest() != entry.entry_sha256:
                raise ValueError("lifecycle journal entry digest mismatch")
            if entry.phase is JournalPhase.INTENT:
                if entry.txid in seen_intents:
                    raise ValueError("duplicate lifecycle journal intent")
                seen_intents[entry.txid] = (entry.operation, entry.handle)
            else:
                if entry.txid not in seen_intents:
                    raise ValueError("lifecycle journal commit without intent")
                if entry.txid in committed:
                    raise ValueError("duplicate lifecycle journal commit")
                if seen_intents[entry.txid] != (entry.operation, entry.handle):
                    raise ValueError("lifecycle journal commit metadata mismatch")
                committed.add(entry.txid)
            previous = entry.entry_sha256
