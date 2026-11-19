from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.x509.oid import NameOID, ObjectIdentifier

from secure_core_mobile.avf_certificate import verify_avf_leaf_claims
from secure_core_mobile.avf_extension import AVF_ATTESTATION_OID


def _len(n):
    return bytes([n]) if n < 128 else b"\x81" + bytes([n])
def _tlv(tag, v):
    return bytes([tag]) + _len(len(v)) + v
def _ext(challenge, secure=True):
    component = _tlv(0x30, _tlv(0x0c,b"payload.apk")+_tlv(0x02,b"\x01")+_tlv(0x04,b"c"*32)+_tlv(0x04,b"a"*32))
    return _tlv(0x30, _tlv(0x04,challenge)+_tlv(0x01,b"\xff" if secure else b"\x00")+_tlv(0x30,component))

def _cert(challenge=b"fresh", secure=True):
    key = ed25519.Ed25519PrivateKey.generate()
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-avf-leaf")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now-timedelta(minutes=1)).not_valid_after(now+timedelta(hours=1))
        .add_extension(x509.UnrecognizedExtension(ObjectIdentifier(AVF_ATTESTATION_OID), _ext(challenge, secure)), critical=False)
        .sign(key, algorithm=None))
    return cert.public_bytes(serialization.Encoding.DER)

def test_extracts_challenge_secure_flag_and_components_from_leaf():
    parsed = verify_avf_leaf_claims(_cert(), expected_challenge=b"fresh")
    assert parsed.is_vm_secure
    assert len(parsed.vm_components) == 1

def test_wrong_challenge_fails_closed():
    with pytest.raises(ValueError, match="challenge"):
        verify_avf_leaf_claims(_cert(), expected_challenge=b"other")

def test_insecure_vm_flag_fails_closed():
    with pytest.raises(ValueError, match="insecure"):
        verify_avf_leaf_claims(_cert(secure=False), expected_challenge=b"fresh")
