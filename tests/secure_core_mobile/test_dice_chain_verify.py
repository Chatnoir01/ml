import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from secure_core_mobile.cose_sign1_payload import parse_cose_sign1
from secure_core_mobile.cose_sign1_verify import sig_structure
from secure_core_mobile.dice_chain_verify import verify_chain, SUBJECT_PUBLIC_KEY


def _head(major,n):
    return bytes(((major<<5)|n,)) if n<24 else bytes(((major<<5)|24,n))
def _i(v):
    n=-1-v
    return bytes((0x20+n,)) if n<24 else bytes((0x38,n))
def _b(v): return _head(2,len(v))+v
def _map(items): return _head(5,len(items))+b"".join(k+v for k,v in items)


def _cose_key(pub):
    n=pub.public_numbers()
    return _map([
        (b"\x01",b"\x02"),(b"\x03",b"\x26"),(_i(-1),b"\x01"),
        (_i(-2),_b(n.x.to_bytes(32,"big"))),(_i(-3),_b(n.y.to_bytes(32,"big"))),
    ])


def _cert(parent,subject):
    payload=_map([(_i(SUBJECT_PUBLIC_KEY),_b(_cose_key(subject.public_key())))])
    protected=b"\xa1\x01\x26"
    base=b"\x84"+_b(protected)+b"\xa0"+_b(payload)+b"\x40"
    e=parse_cose_sign1(base)
    der=parent.sign(sig_structure(e),ec.ECDSA(hashes.SHA256()))
    r,s=decode_dss_signature(der); raw=r.to_bytes(32,"big")+s.to_bytes(32,"big")
    return b"\x84"+_b(protected)+b"\xa0"+_b(payload)+b"\x58\x40"+raw


def test_two_hop_chain_carries_authenticated_subject_key_forward():
    root=ec.generate_private_key(ec.SECP256R1())
    middle=ec.generate_private_key(ec.SECP256R1())
    leaf=ec.generate_private_key(ec.SECP256R1())
    result=verify_chain(root.public_key(),(_cert(root,middle),_cert(middle,leaf)))
    assert result.entries==2
    assert result.leaf_public_key.public_numbers()==leaf.public_key().public_numbers()


def test_second_entry_signed_by_wrong_key_is_rejected():
    root=ec.generate_private_key(ec.SECP256R1())
    middle=ec.generate_private_key(ec.SECP256R1())
    leaf=ec.generate_private_key(ec.SECP256R1())
    attacker=ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(InvalidSignature):
        verify_chain(root.public_key(),(_cert(root,middle),_cert(attacker,leaf)))
