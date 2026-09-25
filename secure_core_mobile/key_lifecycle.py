"""Opaque-handle key lifecycle registry.

Development registry: metadata only. Raw key material is deliberately absent.
"""

from __future__ import annotations
from dataclasses import dataclass
from .compat import StrEnum
from threading import Lock
import secrets


class LifecycleError(RuntimeError):
    pass


class StoredKeyState(StrEnum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    DESTROYED = "DESTROYED"


@dataclass(frozen=True)
class KeyRecord:
    handle: str
    generation: int
    state: StoredKeyState
    provider_id: str


class KeyRegistry:
    def __init__(self) -> None:
        self._records: dict[str, KeyRecord] = {}
        self._lock = Lock()

    def create(self, *, provider_id: str) -> KeyRecord:
        if not provider_id:
            raise LifecycleError("provider_id required")
        with self._lock:
            handle = "scm_" + secrets.token_hex(16)
            record = KeyRecord(handle, 1, StoredKeyState.ACTIVE, provider_id)
            self._records[handle] = record
            return record

    def register(self, *, handle: str, provider_id: str) -> KeyRecord:
        if not handle or not provider_id:
            raise LifecycleError("handle and provider_id required")
        with self._lock:
            if handle in self._records:
                raise LifecycleError("opaque key handle already registered")
            record = KeyRecord(handle, 1, StoredKeyState.ACTIVE, provider_id)
            self._records[handle] = record
            return record

    def get(self, handle: str) -> KeyRecord | None:
        with self._lock:
            return self._records.get(handle)

    def rotate(self, handle: str) -> KeyRecord:
        with self._lock:
            current = self._require(handle)
            if current.state is not StoredKeyState.ACTIVE:
                raise LifecycleError("only active keys may rotate")
            updated = KeyRecord(handle, current.generation + 1, current.state, current.provider_id)
            self._records[handle] = updated
            return updated

    def revoke(self, handle: str) -> KeyRecord:
        return self._change_state(handle, StoredKeyState.REVOKED)

    def destroy(self, handle: str) -> KeyRecord:
        return self._change_state(handle, StoredKeyState.DESTROYED)

    def _change_state(self, handle: str, target: StoredKeyState) -> KeyRecord:
        with self._lock:
            current = self._require(handle)
            if current.state is StoredKeyState.DESTROYED:
                raise LifecycleError("destroyed key is terminal")
            if target is StoredKeyState.REVOKED and current.state is not StoredKeyState.ACTIVE:
                raise LifecycleError("only active keys may revoke")
            updated = KeyRecord(handle, current.generation, target, current.provider_id)
            self._records[handle] = updated
            return updated

    def _require(self, handle: str) -> KeyRecord:
        try:
            return self._records[handle]
        except KeyError as exc:
            raise LifecycleError("unknown opaque key handle") from exc
