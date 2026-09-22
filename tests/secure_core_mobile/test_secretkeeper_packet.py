import pytest
from secure_core_mobile.secretkeeper_packet import (
    ProtectedPacketBinding, SequenceWindow, verify_session_binding,
)


def _packet(seq=0, session=b"session", iv=b"i"*12):
    return ProtectedPacketBinding(session, seq, iv)


def test_packet_requires_aosp_aead_metadata_shape():
    verify_session_binding(b"session", _packet())
    with pytest.raises(ValueError, match="12"):
        _packet(iv=b"short").validate()
    with pytest.raises(ValueError, match="algorithm"):
        ProtectedPacketBinding(b"s", 0, b"i"*12, algorithm=99).validate()


def test_session_id_substitution_fails():
    with pytest.raises(ValueError, match="session mismatch"):
        verify_session_binding(b"expected", _packet(session=b"attacker"))


def test_sequence_window_rejects_replay_and_out_of_order():
    window = SequenceWindow()
    window.consume(0)
    with pytest.raises(ValueError, match="replay"):
        window.consume(0)
    with pytest.raises(ValueError, match="replay"):
        window.consume(2)
    window.consume(1)
