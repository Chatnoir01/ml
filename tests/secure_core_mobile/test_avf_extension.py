from __future__ import annotations
import pytest
from secure_core_mobile.avf_extension import parse_avf_attestation_extension


def _der_len(n):
    return bytes([n]) if n < 128 else b"\x81" + bytes([n])

def _tlv(tag, value):
    return bytes([tag]) + _der_len(len(value)) + value

def _component(name=b"payload.apk", version=1):
    body = _tlv(0x0C, name) + _tlv(0x02, bytes([version])) + _tlv(0x04, b"c"*32) + _tlv(0x04, b"a"*32)
    return _tlv(0x30, body)

def _extension(challenge=b"fresh", secure=True):
    body = _tlv(0x04, challenge) + _tlv(0x01, b"\xff" if secure else b"\x00") + _tlv(0x30, _component())
    return _tlv(0x30, body)

def test_parse_documented_avf_extension_shape():
    parsed = parse_avf_attestation_extension(_extension())
    assert parsed.attestation_challenge == b"fresh"
    assert parsed.is_vm_secure is True
    assert parsed.vm_components[0].name == "payload.apk"
    assert parsed.vm_components[0].security_version == 1

def test_reject_trailing_data_and_noncanonical_boolean():
    with pytest.raises(ValueError, match="trailing"):
        parse_avf_attestation_extension(_extension() + b"x")
    bad = _tlv(0x30, _tlv(0x04,b"c") + _tlv(0x01,b"\x01") + _tlv(0x30,_component()))
    with pytest.raises(ValueError, match="boolean"):
        parse_avf_attestation_extension(bad)
