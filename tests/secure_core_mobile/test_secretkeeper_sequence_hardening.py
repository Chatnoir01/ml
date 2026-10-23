"""Secretkeeper COSE sequence hardening; no native/hardware security claim."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from cryptography.exceptions import InvalidTag

from secure_core_mobile.cose_encrypt0 import (
    Encrypt0Packet,
    ExternalAadMode,
    decrypt,
    decrypt_and_consume,
    encrypt,
    external_aad,
)
from secure_core_mobile.secretkeeper_packet import (
    MAX_SEQUENCE_NUMBER,
    ProtectedPacketBinding,
    SequenceWindow,
)

_KEY = b"k" * 32
_IV = b"v" * 12
_SESSION = b"sid"


def _authenticated(seq: int = 0, *, iv: bytes = _IV) -> Encrypt0Packet:
    return encrypt(
        key=_KEY,
        session_id=_SESSION,
        sequence_number=seq,
        plaintext=b"protected-payload",
        iv=iv,
        aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64,
    )


def test_replay_sensitive_profile_authenticates_sequence_then_consumes() -> None:
    window = SequenceWindow()
    first = _authenticated(0)
    assert decrypt_and_consume(
        key=_KEY, packet=first, expected_session_id=_SESSION, window=window
    ) == b"protected-payload"
    assert window.next_sequence_number == 1
    with pytest.raises(ValueError, match="sequence"):
        decrypt_and_consume(
            key=_KEY, packet=first, expected_session_id=_SESSION, window=window
        )
    assert window.next_sequence_number == 1
    second = _authenticated(1, iv=b"w" * 12)
    assert decrypt_and_consume(
        key=_KEY, packet=second, expected_session_id=_SESSION, window=window
    ) == b"protected-payload"


def test_authenticated_packet_cannot_be_relabelled_as_next_sequence() -> None:
    window = SequenceWindow()
    original = _authenticated(0)
    assert decrypt_and_consume(
        key=_KEY, packet=original, expected_session_id=_SESSION, window=window
    ) == b"protected-payload"
    altered = Encrypt0Packet(replace(original.binding, sequence_number=1), original.ciphertext)
    with pytest.raises(InvalidTag):
        decrypt_and_consume(
            key=_KEY, packet=altered, expected_session_id=_SESSION, window=window
        )
    assert window.next_sequence_number == 1


def test_empty_external_aad_does_not_authenticate_sequence_metadata() -> None:
    """Document the legacy interoperability limitation so it cannot be overclaimed."""
    original = encrypt(
        key=_KEY, session_id=_SESSION, sequence_number=0,
        plaintext=b"legacy", iv=_IV, aad_mode=ExternalAadMode.EMPTY,
    )
    relabelled = Encrypt0Packet(
        replace(original.binding, sequence_number=1), original.ciphertext
    )
    # This operation is allowed ONLY as legacy compatibility, not as a replay-safe API.
    assert decrypt(
        key=_KEY, packet=relabelled,
        expected_session_id=_SESSION, expected_sequence_number=1,
        aad_mode=ExternalAadMode.EMPTY,
    ) == b"legacy"
    with pytest.raises(InvalidTag):
        decrypt_and_consume(
            key=_KEY, packet=relabelled, expected_session_id=_SESSION,
            window=SequenceWindow(),
        )


def test_invalid_tag_does_not_consume_sequence_number() -> None:
    window = SequenceWindow()
    original = _authenticated()
    altered = Encrypt0Packet(
        original.binding,
        original.ciphertext[:-1] + bytes((original.ciphertext[-1] ^ 1,)),
    )
    with pytest.raises(InvalidTag):
        decrypt_and_consume(
            key=_KEY, packet=altered, expected_session_id=_SESSION, window=window,
        )
    assert window.next_sequence_number == 0
    assert decrypt_and_consume(
        key=_KEY, packet=original, expected_session_id=_SESSION, window=window,
    ) == b"protected-payload"


@pytest.mark.parametrize("bad", [-1, True, 1.0, MAX_SEQUENCE_NUMBER + 1, "0"])
def test_binding_rejects_non_uint64_sequence_values(bad: object) -> None:
    with pytest.raises(ValueError, match="uint64"):
        ProtectedPacketBinding(_SESSION, bad, _IV).validate()
    with pytest.raises(ValueError, match="uint64"):
        external_aad(bad, ExternalAadMode.EMPTY)


@pytest.mark.parametrize("bad", [-1, True, MAX_SEQUENCE_NUMBER + 1, "1"])
def test_sequence_window_rejects_non_uint64_values(bad: object) -> None:
    window = SequenceWindow()
    with pytest.raises(ValueError, match="uint64"):
        window.consume(bad)
    assert window.next_sequence_number == 0


def test_seqnum_uint64_maximum_and_counter_exhaustion() -> None:
    window = SequenceWindow()
    window._next = MAX_SEQUENCE_NUMBER  # Test rollover boundary only.
    window.consume(MAX_SEQUENCE_NUMBER)
    assert window.next_sequence_number == MAX_SEQUENCE_NUMBER + 1
    with pytest.raises(ValueError, match="exhausted"):
        window.consume(MAX_SEQUENCE_NUMBER)


def test_sequence_window_consumption_is_atomic_under_concurrency() -> None:
    window = SequenceWindow()
    def consume() -> str:
        try:
            window.consume(0)
            return "accepted"
        except ValueError:
            return "rejected"
    with ThreadPoolExecutor(max_workers=16) as pool:
        outcome = list(pool.map(lambda _n: consume(), range(32)))
    assert outcome.count("accepted") == 1
    assert outcome.count("rejected") == 31
    assert window.next_sequence_number == 1


def test_explicit_empty_iv_rejected_instead_of_regenerated() -> None:
    with pytest.raises(ValueError, match="12 bytes"):
        encrypt(
            key=_KEY, session_id=_SESSION, sequence_number=0,
            plaintext=b"message", iv=b"",
        )


def test_explicit_unsupported_aad_mode_rejected() -> None:
    for mode in ("REQUEST_SEQNUM_U64", None, object()):
        with pytest.raises(ValueError, match="AAD mode"):
            external_aad(0, mode)


def test_invalid_session_id_and_iv_types_rejected() -> None:
    for session in (b"", "sid", b"s" * 65536):
        with pytest.raises(ValueError, match="session id"):
            ProtectedPacketBinding(session, 0, _IV).validate()
    for iv in (None, "v" * 12, b"short"):
        with pytest.raises(ValueError, match="12 bytes"):
            ProtectedPacketBinding(_SESSION, 0, iv).validate()


def test_secure_decrypt_requires_explicit_sequence_window() -> None:
    with pytest.raises(TypeError, match="window"):
        decrypt_and_consume(
            key=_KEY, packet=_authenticated(),
            expected_session_id=_SESSION, window=None,
        )
