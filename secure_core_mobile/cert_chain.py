"""Explicit certificate-chain validation for pVM attestation.

Trust anchors are injected DER certificates. This module does not ship or infer
Android/AVF roots; production roots must be provisioned from authoritative
platform material.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa, padding


@dataclass(frozen=True)
class CertificateTrustStore:
    anchors_der: tuple[bytes, ...]

    def anchors(self) -> tuple[x509.Certificate, ...]:
        return tuple(x509.load_der_x509_certificate(x) for x in self.anchors_der)


def _verify_cert_signature(cert: x509.Certificate, issuer: x509.Certificate) -> None:
    key = issuer.public_key()
    sig = cert.signature
    data = cert.tbs_certificate_bytes
    try:
        if isinstance(key, ed25519.Ed25519PublicKey):
            key.verify(sig, data)
        elif isinstance(key, ec.EllipticCurvePublicKey):
            key.verify(sig, data, ec.ECDSA(cert.signature_hash_algorithm))
        elif isinstance(key, rsa.RSAPublicKey):
            key.verify(sig, data, padding.PKCS1v15(), cert.signature_hash_algorithm)
        else:
            raise ValueError("unsupported certificate public key type")
    except InvalidSignature as exc:
        raise ValueError("certificate signature invalid") from exc


def _check_time(cert: x509.Certificate, now: datetime) -> None:
    start = cert.not_valid_before_utc
    end = cert.not_valid_after_utc
    if now < start or now > end:
        raise ValueError("certificate outside validity period")


def verify_certificate_chain(
    chain_der: tuple[bytes, ...],
    trust_store: CertificateTrustStore,
    *,
    now: datetime | None = None,
) -> bool:
    if not chain_der:
        raise ValueError("empty certificate chain")
    certs = tuple(x509.load_der_x509_certificate(x) for x in chain_der)
    anchors = trust_store.anchors()
    if not anchors:
        raise ValueError("empty certificate trust store")
    current_time = now or datetime.now(timezone.utc)
    for cert in certs:
        _check_time(cert, current_time)
    for child, issuer in zip(certs, certs[1:]):
        if child.issuer != issuer.subject:
            raise ValueError("certificate issuer mismatch")
        _verify_cert_signature(child, issuer)
    tail = certs[-1]
    for anchor in anchors:
        _check_time(anchor, current_time)
        if tail.fingerprint(hashes.SHA256()) == anchor.fingerprint(hashes.SHA256()):
            return True
        if tail.issuer == anchor.subject:
            _verify_cert_signature(tail, anchor)
            return True
    raise ValueError("certificate chain does not terminate at trusted anchor")
