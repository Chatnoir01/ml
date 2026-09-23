import pytest
from secure_core_mobile.cose_sign1_payload import *


def test_extracts_embedded_cbor_payload_from_cose_sign1():
    # [protected=b"", unprotected={}, payload={1:7}, signature=b"sig"]
    encoded=bytes.fromhex("8440a043a1010743736967")
    assert payload_value_from_cose_sign1(encoded)=={1:7}


def test_missing_payload_is_rejected():
    # null payload is structurally legal COSE but invalid for AOSP DICE policy.
    # Our strict decoder intentionally has no simple-value/null support, so it fails closed.
    with pytest.raises((ValueError,CborDecodeError)):
        parse_cose_sign1(bytes.fromhex("8440a0f643736967"))


def test_trailing_payload_bytes_and_duplicate_map_keys_are_rejected():
    trailing=bytes.fromhex("8440a044a101070043736967")
    with pytest.raises(CborDecodeError,match="trailing"):
        payload_value_from_cose_sign1(trailing)
    duplicate=bytes.fromhex("8440a045a20101010243736967")
    with pytest.raises(CborDecodeError,match="duplicate"):
        payload_value_from_cose_sign1(duplicate)


def test_signature_is_not_misrepresented_as_verified():
    entry=parse_cose_sign1(bytes.fromhex("8440a043a1010740"))
    assert entry.signature==b""
    assert payload_value_from_cose_sign1(bytes.fromhex("8440a043a1010740"))=={1:7}
