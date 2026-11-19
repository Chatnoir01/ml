"""Fail-closed pVM verifier pipeline using established cryptographic primitives.

This verifies a supplied leaf certificate signature over the canonical
statement. It does NOT yet validate an Android/AVF certificate chain to a
platform trust anchor; therefore verified remains false until that stage exists.
"""

from __future__ import annotations
from dataclasses import dataclass

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa, padding
from cryptography.hazmat.primitives import hashes

from .cert_chain import CertificateTrustStore, verify_certificate_chain
from .pvm_attestation import (
    PvmAttestationStatement, PvmTrustStore, validate_statement_shape,
    verify_challenge_binding,
)


@dataclass(frozen=True)
class PvmVerificationResult:
    statement_valid: bool
    measurement_trusted: bool
    signature_verified: bool
    chain_verified: bool
    reason: str

    @property
    def verified(self) -> bool:
        return (
            self.statement_valid and self.measurement_trusted
            and self.signature_verified and self.chain_verified
        )


def _verify_leaf_signature(statement: PvmAttestationStatement, signature: bytes, cert_der: bytes) -> bool:
    cert = x509.load_der_x509_certificate(cert_der)
    key = cert.public_key()
    message = statement.canonical_bytes()
    try:
        if isinstance(key, ed25519.Ed25519PublicKey):
            key.verify(signature, message)
        elif isinstance(key, ec.EllipticCurvePublicKey):
            key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
        elif isinstance(key, rsa.RSAPublicKey):
            key.verify(signature, message, padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ), hashes.SHA256())
        else:
            raise ValueError("unsupported attestation public key type")
    except InvalidSignature:
        return False
    return True


class PvmAttestationVerifier:
    def __init__(self, trust_store: PvmTrustStore, certificate_trust_store: CertificateTrustStore | None = None) -> None:
        self._trust_store = trust_store
        self._certificate_trust_store = certificate_trust_store

    def verify(self, *, statement: PvmAttestationStatement, challenge: bytes,
               signature: bytes, certificate_chain: tuple[bytes, ...]) -> PvmVerificationResult:
        validate_statement_shape(statement)
        verify_challenge_binding(statement, challenge)
        trusted = self._trust_store.lookup(statement.measurement_sha256) is not None
        if not trusted:
            return PvmVerificationResult(True, False, False, False, "measurement-not-trusted")
        if not signature or not certificate_chain:
            return PvmVerificationResult(True, True, False, False, "missing-platform-signature-evidence")
        try:
            signature_ok = _verify_leaf_signature(statement, signature, certificate_chain[0])
        except (ValueError, TypeError):
            return PvmVerificationResult(True, True, False, False, "invalid-leaf-certificate")
        if not signature_ok:
            return PvmVerificationResult(True, True, False, False, "statement-signature-invalid")
        if self._certificate_trust_store is None:
            return PvmVerificationResult(True, True, True, False, "certificate-trust-store-not-configured")
        try:
            chain_ok = verify_certificate_chain(certificate_chain, self._certificate_trust_store)
        except ValueError:
            return PvmVerificationResult(True, True, True, False, "platform-certificate-chain-invalid")
        if not chain_ok:
            return PvmVerificationResult(True, True, True, False, "platform-certificate-chain-invalid")
        return PvmVerificationResult(True, True, True, True, "cryptographic-chain-verified")
