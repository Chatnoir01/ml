"""Experimental Secretkeeper session invariants (no hardware assurance)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier
from time import sleep

import pytest
from cryptography.exceptions import InvalidTag

from secure_core_mobile.cose_encrypt0 import ExternalAadMode, Encrypt0Packet, encrypt
from secure_core_mobile.secretkeeper_packet import MAX_SEQUENCE_NUMBER
from secure_core_mobile.sk_session import SecretkeeperSessionCore


REQUEST_KEY = b"E" * 32
RESPONSE_KEY = b"D" * 32
SESSION = b"session-xyz"


def _session(**kwargs) -> SecretkeeperSessionCore:
    return SecretkeeperSessionCore(
        REQUEST_KEY, RESPONSE_KEY, SESSION, **kwargs
    )


def _response(sequence: int, *, iv: bytes | None = None) -> Encrypt0Packet:
    return encrypt(
        key=RESPONSE_KEY, session_id=SESSION, sequence_number=sequence,
        plaintext=f"response-{sequence}".encode(),
        iv=(sequence + 1).to_bytes(12, "big") if iv is None else iv,
        aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64,
    )


def test_session_rejects_legacy_unauthenticated_sequence_mode() -> None:
    with pytest.raises(ValueError, match="authenticated sequence"):
        _session(aad_mode=ExternalAadMode.EMPTY)
    with pytest.raises(ValueError, match="authenticated sequence"):
        _session(aad_mode="REQUEST_SEQNUM_U64")


def test_equal_directional_keys_rejected() -> None:
    with pytest.raises(ValueError, match="distinct"):
        SecretkeeperSessionCore(REQUEST_KEY, REQUEST_KEY, SESSION)


def test_session_repr_never_discloses_raw_key_material() -> None:
    session = _session()
    rendered = repr(session)
    assert "SecretkeeperSessionCore" in rendered
    assert "EEEEEEEE" not in rendered
    assert "DDDDDDDD" not in rendered


def test_initial_sequences_must_start_at_zero() -> None:
    with pytest.raises(ValueError, match="start at zero"):
        _session(outgoing_sequence=1)
    with pytest.raises(ValueError, match="start at zero"):
        _session(incoming_sequence=1)
    with pytest.raises(ValueError, match="start at zero"):
        _session(outgoing_sequence=True)


def test_explicit_outgoing_iv_reuse_fails_before_counter_consumption() -> None:
    session = _session()
    packet = session.protect_request(b"first", iv=b"1" * 12)
    assert packet.binding.sequence_number == 0
    with pytest.raises(ValueError, match="IV reused"):
        session.protect_request(b"second", iv=b"1" * 12)
    assert session.outgoing_sequence == 1
    packet2 = session.protect_request(b"second", iv=b"2" * 12)
    assert packet2.binding.sequence_number == 1


def test_bad_outgoing_iv_does_not_consume_counter() -> None:
    session = _session()
    with pytest.raises(ValueError, match="12 bytes"):
        session.protect_request(b"x", iv=b"")
    assert session.outgoing_sequence == 0


def test_outgoing_sequence_exhaustion_is_explicit() -> None:
    session = _session()
    session.outgoing_sequence = MAX_SEQUENCE_NUMBER
    packet = session.protect_request(b"last", iv=b"i" * 12)
    assert packet.binding.sequence_number == MAX_SEQUENCE_NUMBER
    with pytest.raises(ValueError, match="exhausted"):
        session.protect_request(b"too late", iv=b"j" * 12)


def test_invalid_response_does_not_advance_counter_and_retry_can_succeed() -> None:
    session = _session()
    good = _response(0)
    tampered = Encrypt0Packet(
        good.binding,
        good.ciphertext[:-1] + bytes((good.ciphertext[-1] ^ 1,)),
    )
    with pytest.raises(InvalidTag):
        session.open_response(tampered)
    assert session.incoming_sequence == 0
    assert session.open_response(good) == b"response-0"
    assert session.incoming_sequence == 1


def test_relabelled_sequence_rejected_under_aad() -> None:
    session = _session()
    assert session.open_response(_response(0)) == b"response-0"
    packet = _response(0)
    relabelled = Encrypt0Packet(
        replace(packet.binding, sequence_number=1), packet.ciphertext,
    )
    with pytest.raises(InvalidTag):
        session.open_response(relabelled)
    assert session.incoming_sequence == 1


def test_receive_state_mutation_fails_closed() -> None:
    session = _session()
    session.incoming_sequence = 1
    with pytest.raises(ValueError, match="counter state mismatch"):
        session.open_response(_response(0))


def test_parallel_protect_request_numbers_are_unique_and_ordered() -> None:
    session = _session()
    def make_packet(index: int):
        return session.protect_request(
            f"payload-{index}".encode(), iv=(index + 1).to_bytes(12, "big")
        )
    with ThreadPoolExecutor(max_workers=12) as pool:
        packets = list(pool.map(make_packet, range(30)))
    assert sorted(packet.binding.sequence_number for packet in packets) == list(range(30))
    assert len({packet.binding.iv for packet in packets}) == 30
    assert session.outgoing_sequence == 30


def test_simultaneous_same_iv_allows_only_one_success() -> None:
    session = _session()
    def attempt(index: int) -> str:
        try:
            session.protect_request(f"{index}".encode(), iv=b"shared-IV-12")
            return "accepted"
        except ValueError:
            return "rejected"
    with ThreadPoolExecutor(max_workers=12) as pool:
        result = list(pool.map(attempt, range(24)))
    assert result.count("accepted") == 1
    assert result.count("rejected") == 23
    assert session.outgoing_sequence == 1


def test_full_exchanges_are_serialized_and_responses_match_sequence() -> None:
    session = _session()
    class MockTransport:
        def transact(self, request: Encrypt0Packet) -> Encrypt0Packet:
            if request.binding.sequence_number == 0:
                sleep(0.01)
            return _response(request.binding.sequence_number)
    with ThreadPoolExecutor(max_workers=8) as pool:
        answers = list(pool.map(
            lambda index: session.request(MockTransport(), str(index).encode()),
            range(8),
        ))
    assert sorted(answers) == sorted(f"response-{i}".encode() for i in range(8))
    assert session.outgoing_sequence == session.incoming_sequence == 8


def test_session_refuses_nonbyte_keys_or_unbounded_session_id() -> None:
    with pytest.raises(ValueError, match="AES-256"):
        SecretkeeperSessionCore("E" * 32, RESPONSE_KEY, SESSION)
    with pytest.raises(ValueError, match="session id"):
        SecretkeeperSessionCore(REQUEST_KEY, RESPONSE_KEY, b"")
    with pytest.raises(ValueError, match="session id"):
        SecretkeeperSessionCore(REQUEST_KEY, RESPONSE_KEY, b"a" * 65536)
