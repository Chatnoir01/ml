import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from secure_core_mobile.cose_sign1_payload import parse_cose_sign1
from secure_core_mobile.cose_sign1_verify import sig_structure, verify_es256


def _signed(private,payload=b"\xa1\x01\x07"):
    protected=b"\xa1\x01\x26"  # {1:-7}
    # temporary valid shape with empty signature to build Sig_structure
    base=b"\x84\x43"+protected+b"\xa0"+bytes((0x40+len(payload),))+payload+b"\x40"
    entry=parse_cose_sign1(base)
    der=private.sign(sig_structure(entry),ec.ECDSA(hashes.SHA256()))
    r,s=decode_dss_signature(der)
    raw=r.to_bytes(32,"big")+s.to_bytes(32,"big")
    return b"\x84\x43"+protected+b"\xa0"+bytes((0x40+len(payload),))+payload+b"\x58\x40"+raw


def test_valid_es256_cose_sign1_verifies():
    key=ec.generate_private_key(ec.SECP256R1())
    encoded=_signed(key)
    assert verify_es256(encoded,key.public_key()).payload==b"\xa1\x01\x07"


def test_payload_tamper_fails_signature():
    key=ec.generate_private_key(ec.SECP256R1())
    encoded=bytearray(_signed(key))
    encoded[9]^=1
    with pytest.raises(InvalidSignature):
        verify_es256(bytes(encoded),key.public_key())


def test_wrong_parent_key_fails_signature():
    signer=ec.generate_private_key(ec.SECP256R1())
    other=ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(InvalidSignature):
        verify_es256(_signed(signer),other.public_key())


def test_wrong_algorithm_is_rejected_before_crypto():
    key=ec.generate_private_key(ec.SECP256R1())
    encoded=bytearray(_signed(key))
    encoded[4]=0x27  # protected map value becomes -8
    with pytest.raises(ValueError,match="ES256"):
        verify_es256(bytes(encoded),key.public_key())
