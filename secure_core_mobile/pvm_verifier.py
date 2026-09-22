"""Fail-closed pVM verifier pipeline."""

from __future__ import annotations
from dataclasses import dataclass

from .pvm_attestation import (
    PvmAttestationStatement, PvmTrustStore, validate_statement_shape,
    verify_challenge_binding,
)


@dataclass(frozen=True)
class PvmVerificationResult:
    statement_valid: bool
    measurement_trusted: bool
    signature_verified: bool
    reason: str

    @property
    def verified(self) -> bool:
        return self.statement_valid and self.measurement_trusted and self.signature_verified


class PvmAttestationVerifier:
    def __init__(self, trust_store: PvmTrustStore) -> None:
        self._trust_store = trust_store

    def verify(self, *, statement: PvmAttestationStatement, challenge: bytes,
               signature: bytes, certificate_chain: tuple[bytes, ...]) -> PvmVerificationResult:
        validate_statement_shape(statement)
        verify_challenge_binding(statement, challenge)
        trusted = self._trust_store.lookup(statement.measurement_sha256) is not None
        if not trusted:
            return PvmVerificationResult(True, False, False, "measurement-not-trusted")
        if not signature or not certificate_chain:
            return PvmVerificationResult(True, True, False, "missing-platform-signature-evidence")
        # Android/AVF certificate-chain and signature verification is not implemented.
        # Never turn structurally plausible evidence into verified platform evidence.
        return PvmVerificationResult(True, True, False, "platform-signature-verification-not-implemented")
