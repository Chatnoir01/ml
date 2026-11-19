from __future__ import annotations
from dataclasses import replace
import pytest

from secure_core_mobile.channel import SessionVerifier, authenticate_frame
from secure_core_mobile.rpc import build_envelope


KEY = b"development-test-session-key"


def _frame(sequence=0, payload=b"x"):
    envelope = build_envelope(
        request_id=f"r{sequence}", operation="sign", key_handle="scm_x",
        policy_version=1, nonce=f"n{sequence}", payload=payload,
    )
    return authenticate_frame(
        session_id="s1", sequence=sequence, envelope=envelope, key=KEY
    )


def test_authenticated_frame_round_trip():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    envelope = verifier.verify_and_decode(_frame())
    assert envelope.request_id == "r0"


def test_frame_replay_is_rejected():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    frame = _frame()
    verifier.verify_and_decode(frame)
    with pytest.raises(ValueError, match="replayed"):
        verifier.verify_and_decode(frame)


def test_skipped_sequence_is_rejected():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    with pytest.raises(ValueError, match="skipped"):
        verifier.verify_and_decode(_frame(sequence=1))


def test_session_substitution_is_rejected():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    forged = replace(_frame(), session_id="other")
    with pytest.raises(ValueError, match="session"):
        verifier.verify_and_decode(forged)


def test_envelope_tampering_breaks_authentication():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    frame = _frame()
    forged = replace(frame, envelope=frame.envelope.replace(b'"sign"', b'"ping"'))
    with pytest.raises(ValueError, match="authentication"):
        verifier.verify_and_decode(forged)


def test_tag_tampering_breaks_authentication():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    forged = replace(_frame(), tag_sha256="0" * 64)
    with pytest.raises(ValueError, match="authentication"):
        verifier.verify_and_decode(forged)


def test_failed_authentication_does_not_advance_sequence():
    verifier = SessionVerifier(session_id="s1", key=KEY)
    good = _frame()
    bad = replace(good, tag_sha256="0" * 64)
    with pytest.raises(ValueError):
        verifier.verify_and_decode(bad)
    assert verifier.verify_and_decode(good).request_id == "r0"
