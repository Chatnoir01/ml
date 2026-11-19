import pytest
from cryptography.exceptions import InvalidTag

from secure_core_mobile.cose_encrypt0 import encrypt, ExternalAadMode
from secure_core_mobile.sk_session import SecretkeeperSessionCore


ENC=b"e"*32
DEC=b"d"*32
SID=b"session"


def test_independent_request_and_response_counters():
    s=SecretkeeperSessionCore(ENC,DEC,SID)
    p0=s.protect_request(b"a",iv=b"0"*12)
    p1=s.protect_request(b"b",iv=b"1"*12)
    assert p0.binding.sequence_number == 0
    assert p1.binding.sequence_number == 1
    assert s.incoming_sequence == 0

    response=encrypt(key=DEC,session_id=SID,sequence_number=0,plaintext=b"ok",
                     iv=b"2"*12,aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64)
    assert s.open_response(response)==b"ok"
    assert s.incoming_sequence == 1


def test_response_encrypted_with_request_key_is_rejected():
    s=SecretkeeperSessionCore(ENC,DEC,SID)
    response=encrypt(key=ENC,session_id=SID,sequence_number=0,plaintext=b"bad",
                     iv=b"2"*12,aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64)
    with pytest.raises(InvalidTag):
        s.open_response(response)
    assert s.incoming_sequence == 0


def test_failed_response_does_not_consume_sequence():
    s=SecretkeeperSessionCore(ENC,DEC,SID)
    wrong=encrypt(key=DEC,session_id=SID,sequence_number=1,plaintext=b"x",
                  iv=b"2"*12,aad_mode=ExternalAadMode.REQUEST_SEQNUM_U64)
    with pytest.raises(ValueError,match="sequence"):
        s.open_response(wrong)
    assert s.incoming_sequence == 0
