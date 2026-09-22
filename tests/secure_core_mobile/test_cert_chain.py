from __future__ import annotations
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID

from secure_core_mobile.cert_chain import CertificateTrustStore, verify_certificate_chain


def _cert(subject, issuer, public_key, issuer_key, *, ca):
    now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
    issuer_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer)])
    return (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(issuer_name).public_key(public_key)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
        .sign(issuer_key, algorithm=None)
    )


def _der(cert):
    return cert.public_bytes(serialization.Encoding.DER)


def test_leaf_to_explicit_root_anchor_verifies():
    root_key = ed25519.Ed25519PrivateKey.generate()
    leaf_key = ed25519.Ed25519PrivateKey.generate()
    root = _cert("root", "root", root_key.public_key(), root_key, ca=True)
    leaf = _cert("leaf", "root", leaf_key.public_key(), root_key, ca=False)
    assert verify_certificate_chain((_der(leaf),), CertificateTrustStore((_der(root),)))


def test_untrusted_root_is_rejected():
    root_key = ed25519.Ed25519PrivateKey.generate()
    other_key = ed25519.Ed25519PrivateKey.generate()
    leaf_key = ed25519.Ed25519PrivateKey.generate()
    root = _cert("root", "root", root_key.public_key(), root_key, ca=True)
    other = _cert("other", "other", other_key.public_key(), other_key, ca=True)
    leaf = _cert("leaf", "root", leaf_key.public_key(), root_key, ca=False)
    with pytest.raises(ValueError, match="trusted anchor"):
        verify_certificate_chain((_der(leaf),), CertificateTrustStore((_der(other),)))


def test_empty_trust_store_fails_closed():
    root_key = ed25519.Ed25519PrivateKey.generate()
    root = _cert("root", "root", root_key.public_key(), root_key, ca=True)
    with pytest.raises(ValueError, match="trust store"):
        verify_certificate_chain((_der(root),), CertificateTrustStore(()))
