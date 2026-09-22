"""Opaque-handle development crypto provider using established primitives.

Private keys never leave the provider API. This is real cryptography for the
development boundary, not hardware-backed storage.
"""

from __future__ import annotations
from dataclasses import dataclass
import secrets
from threading import Lock

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


@dataclass(frozen=True)
class PublicKeyRecord:
    handle: str
    public_key_raw: bytes


class OpaqueEd25519Provider:
    def __init__(self) -> None:
        self._keys: dict[str, ed25519.Ed25519PrivateKey] = {}
        self._lock = Lock()
        self.call_count = 0

    def create_key(self) -> PublicKeyRecord:
        private = ed25519.Ed25519PrivateKey.generate()
        handle = "scm_ed25519_" + secrets.token_hex(16)
        with self._lock:
            self._keys[handle] = private
        return PublicKeyRecord(handle, private.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw))

    def public_key(self, handle: str) -> bytes:
        with self._lock:
            key = self._keys.get(handle)
            if key is None:
                raise KeyError("unknown key handle")
            return key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)

    def operate(self, *, operation: str, key_handle: str, payload: bytes) -> bytes:
        if operation != "sign":
            raise ValueError("unsupported opaque-provider operation")
        with self._lock:
            key = self._keys.get(key_handle)
            if key is None:
                raise KeyError("unknown key handle")
            self.call_count += 1
            return key.sign(payload)

    def destroy(self, handle: str) -> None:
        with self._lock:
            if self._keys.pop(handle, None) is None:
                raise KeyError("unknown key handle")
