"""Extract and verify documented AVF remote-attestation leaf claims."""

from __future__ import annotations
import hmac

from cryptography import x509
from cryptography.x509.oid import ObjectIdentifier

from .avf_extension import AVF_ATTESTATION_OID, AvfAttestationExtension, parse_avf_attestation_extension


def extract_avf_extension(leaf_der: bytes) -> AvfAttestationExtension:
    cert = x509.load_der_x509_certificate(leaf_der)
    try:
        ext = cert.extensions.get_extension_for_oid(ObjectIdentifier(AVF_ATTESTATION_OID))
    except x509.ExtensionNotFound as exc:
        raise ValueError("AVF attestation extension missing") from exc
    raw = getattr(ext.value, "value", None)
    if not isinstance(raw, bytes):
        raise ValueError("AVF attestation extension is not raw DER")
    return parse_avf_attestation_extension(raw)


def verify_avf_leaf_claims(leaf_der: bytes, *, expected_challenge: bytes) -> AvfAttestationExtension:
    parsed = extract_avf_extension(leaf_der)
    if not hmac.compare_digest(parsed.attestation_challenge, expected_challenge):
        raise ValueError("AVF attestation challenge mismatch")
    if not parsed.is_vm_secure:
        raise ValueError("AVF attestation reports insecure VM")
    if not parsed.vm_components:
        raise ValueError("AVF attestation contains no VM components")
    return parsed
