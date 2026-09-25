"""Strict pVM attestation statement and trust-store contract.

This is a verifier framework, not Android AVF attestation verification.
Synthetic statements can never produce verified isolation.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json


ATTESTATION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PvmAttestationStatement:
    schema_version: int
    boundary_id: str
    measurement_sha256: str
    challenge_sha256: str
    public_key_sha256: str
    authorization_state_inside_boundary: bool
    monotonic_state_inside_boundary: bool

    def canonical_bytes(self) -> bytes:
        return json.dumps({
            "schema_version": self.schema_version,
            "boundary_id": self.boundary_id,
            "measurement_sha256": self.measurement_sha256,
            "challenge_sha256": self.challenge_sha256,
            "public_key_sha256": self.public_key_sha256,
            "authorization_state_inside_boundary": self.authorization_state_inside_boundary,
            "monotonic_state_inside_boundary": self.monotonic_state_inside_boundary,
        }, sort_keys=True, separators=(",", ":")).encode()


@dataclass(frozen=True)
class TrustedMeasurement:
    measurement_sha256: str
    release_id: str


class PvmTrustStore:
    def __init__(self, entries: tuple[TrustedMeasurement, ...]) -> None:
        self._entries = {e.measurement_sha256: e for e in entries}

    def lookup(self, measurement_sha256: str) -> TrustedMeasurement | None:
        return self._entries.get(measurement_sha256)


def validate_statement_shape(statement: PvmAttestationStatement) -> None:
    if statement.schema_version != ATTESTATION_SCHEMA_VERSION:
        raise ValueError("unsupported pVM attestation schema")
    if not statement.boundary_id:
        raise ValueError("missing boundary id")
    for name in ("measurement_sha256", "challenge_sha256", "public_key_sha256"):
        value = getattr(statement, name)
        if len(value) != 64:
            raise ValueError(f"invalid {name}")
        try:
            bytes.fromhex(value)
        except ValueError as exc:
            raise ValueError(f"invalid {name}") from exc


def verify_challenge_binding(statement: PvmAttestationStatement, challenge: bytes) -> None:
    expected = hashlib.sha256(challenge).hexdigest()
    if not hmac.compare_digest(expected, statement.challenge_sha256):
        raise ValueError("pVM attestation challenge mismatch")
