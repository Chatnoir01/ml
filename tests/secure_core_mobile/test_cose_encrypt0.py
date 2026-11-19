import pytest
from cryptography.exceptions import InvalidTag

from secure_core_mobile.cose_encrypt0 import decrypt, encrypt, Encrypt0Packet, ExternalAadMode
from secure_core_mobile.secretkeeper_packet import ProtectedPacketBinding


KEY = b"k"*32
IV = b"i"*12


def test_encrypt0_roundtrip_is_bound_to_session_and_sequence():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=7, plaintext=b"secret-request", iv=IV)
    assert decrypt(key=KEY, packet=packet, expected_session_id=b"sid", expected_sequence_number=7) == b"secret-request"


def test_wrong_session_and_sequence_fail_before_decryption():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=7, plaintext=b"x", iv=IV)
    with pytest.raises(ValueError, match="session"):
        decrypt(key=KEY, packet=packet, expected_session_id=b"other", expected_sequence_number=7)
    with pytest.raises(ValueError, match="sequence"):
        decrypt(key=KEY, packet=packet, expected_session_id=b"sid", expected_sequence_number=8)


def test_ciphertext_tamper_fails_authentication():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=0, plaintext=b"x", iv=IV)
    tampered = Encrypt0Packet(packet.binding, packet.ciphertext[:-1] + bytes([packet.ciphertext[-1] ^ 1]))
    with pytest.raises(InvalidTag):
        decrypt(key=KEY, packet=tampered, expected_session_id=b"sid", expected_sequence_number=0)


def test_iv_tamper_fails_authentication():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=0, plaintext=b"x", iv=IV)
    binding = ProtectedPacketBinding(b"sid", 0, b"j"*12)
    with pytest.raises(InvalidTag):
        decrypt(key=KEY, packet=Encrypt0Packet(binding, packet.ciphertext), expected_session_id=b"sid", expected_sequence_number=0)


def test_current_aosp_empty_external_aad_mode_roundtrip():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=0, plaintext=b"x", iv=IV)
    assert decrypt(key=KEY, packet=packet, expected_session_id=b"sid", expected_sequence_number=0) == b"x"

def test_seqnum_aad_branch_is_explicit_and_not_interchangeable():
    packet = encrypt(key=KEY, session_id=b"sid", sequence_number=7, plaintext=b"x", iv=IV,
                     aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64)
    with pytest.raises(InvalidTag):
        decrypt(key=KEY, packet=packet, expected_session_id=b"sid", expected_sequence_number=7,
                aad_mode=ExternalAadMode.EMPTY)
