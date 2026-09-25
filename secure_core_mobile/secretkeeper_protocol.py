"""Strict SecretManagement request model following AOSP SecretManagement.cddl.

This module validates protocol sizes/opcodes before any Android transport.
Actual CBOR encoding and AuthGraph encryption belong to the native client.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum


class SecretManagementOpcode(IntEnum):
    GET_VERSION = 1
    STORE_SECRET = 2
    GET_SECRET = 3


SECRET_ID_BYTES = 64
SECRET_BYTES = 32


@dataclass(frozen=True)
class StoreSecretRequest:
    secret_id: bytes
    secret: bytes
    sealing_policy_cbor: bytes

    def validate(self) -> None:
        if len(self.secret_id) != SECRET_ID_BYTES:
            raise ValueError("Secretkeeper secret id must be 64 bytes")
        if len(self.secret) != SECRET_BYTES:
            raise ValueError("Secretkeeper secret must be 32 bytes")
        if not self.sealing_policy_cbor:
            raise ValueError("Secretkeeper sealing policy is required")


@dataclass(frozen=True)
class GetSecretRequest:
    secret_id: bytes
    updated_sealing_policy_cbor: bytes | None = None

    def validate(self) -> None:
        if len(self.secret_id) != SECRET_ID_BYTES:
            raise ValueError("Secretkeeper secret id must be 64 bytes")
        if self.updated_sealing_policy_cbor == b"":
            raise ValueError("empty updated sealing policy is invalid")
