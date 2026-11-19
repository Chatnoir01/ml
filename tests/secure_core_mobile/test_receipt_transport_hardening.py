from __future__ import annotations
import pytest

from secure_core_mobile.receipts import authorization_receipt
from secure_core_mobile.rpc import build_envelope
from secure_core_mobile.transport import decode_envelope, encode_envelope, MAX_FRAME_BYTES


@pytest.mark.parametrize("payload", [
    {"nested": {"private_key": "x"}},
    {"items": [{"password": "x"}]},
    {"recovery_phrase": "x"},
    {"private-key-material": "x"},
])
def test_nested_or_variant_secret_fields_are_rejected(payload):
    with pytest.raises(ValueError, match="secret-bearing"):
        authorization_receipt(payload)


def test_raw_bytes_are_rejected_from_receipts():
    with pytest.raises(ValueError, match="raw bytes"):
        authorization_receipt({"safe_name": b"not-loggable"})


def test_transport_round_trip_preserves_canonical_envelope():
    envelope = build_envelope(
        request_id="r1", operation="sign", key_handle="scm_x",
        policy_version=1, nonce="n1", payload=b"x",
    )
    decoded = decode_envelope(encode_envelope(envelope))
    assert decoded == envelope
    assert decoded.sha256 == envelope.sha256


def test_transport_rejects_unknown_fields():
    frame = b'{"version":1,"method":"authorize_and_operate","request_id":"r","operation":"sign","key_handle":"k","policy_version":1,"nonce":"n","payload_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","extra":true}'
    with pytest.raises(ValueError, match="schema"):
        decode_envelope(frame)


def test_transport_rejects_oversized_and_malformed_frames():
    with pytest.raises(ValueError, match="size"):
        decode_envelope(b"x" * (MAX_FRAME_BYTES + 1))
    with pytest.raises(ValueError, match="malformed"):
        decode_envelope(b"{not-json")
