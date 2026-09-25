"""Canonical evidence manifest binding executable security components."""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class EvidenceManifest:
    schema_version: int
    boundary_evidence_sha256: str
    trust_policy_sha256: str
    protocol_version: int
    monotonic_backend: str
    hostile_host_ready: bool

    def canonical_bytes(self) -> bytes:
        return json.dumps({
            "schema_version": self.schema_version,
            "boundary_evidence_sha256": self.boundary_evidence_sha256,
            "trust_policy_sha256": self.trust_policy_sha256,
            "protocol_version": self.protocol_version,
            "monotonic_backend": self.monotonic_backend,
            "hostile_host_ready": self.hostile_host_ready,
        }, sort_keys=True, separators=(",", ":")).encode()

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def validate(self) -> None:
        if self.schema_version != 1 or self.protocol_version <= 0:
            raise ValueError("invalid evidence manifest version")
        for value in (self.boundary_evidence_sha256, self.trust_policy_sha256):
            if len(value) != 64:
                raise ValueError("invalid evidence digest")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise ValueError("invalid evidence digest") from exc
        if not self.monotonic_backend:
            raise ValueError("missing monotonic backend identity")
