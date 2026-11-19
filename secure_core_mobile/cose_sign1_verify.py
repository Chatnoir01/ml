"""Cryptographic COSE_Sign1 verifier for the Secure Core DICE subset.

Supports ES256 (-7) with a P-256 parent key. It verifies the exact COSE
Sig_structure ["Signature1", protected, external_aad, payload].
Successful verification is cryptographic evidence only; it is not by itself
Android/Secretkeeper platform provenance.
"""
from __future__ import annotations
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from .cose_sign1_payload import CoseSign1Entry, decode_one, parse_cose_sign1

ES256=-7


def _head(major:int,n:int)->bytes:
    if n<24:return bytes(((major<<5)|n,))
    if n<=0xff:return bytes(((major<<5)|24,n))
    if n<=0xffff:return bytes(((major<<5)|25,))+n.to_bytes(2,"big")
    raise ValueError("CBOR field too large")


def _bstr(v:bytes)->bytes:return _head(2,len(v))+v
def _tstr(v:str)->bytes:
    b=v.encode();return _head(3,len(b))+b


def sig_structure(entry:CoseSign1Entry,external_aad:bytes=b"")->bytes:
    return b"\x84"+_tstr("Signature1")+_bstr(entry.protected)+_bstr(external_aad)+_bstr(entry.payload)


def _protected_algorithm(protected:bytes)->int:
    headers=decode_one(protected)
    if not isinstance(headers,dict) or headers.get(1)!=ES256:
        raise ValueError("COSE_Sign1 protected alg must be ES256")
    return ES256


def verify_es256(encoded:bytes,parent_key:ec.EllipticCurvePublicKey,external_aad:bytes=b"")->CoseSign1Entry:
    entry=parse_cose_sign1(encoded)
    _protected_algorithm(entry.protected)
    if not isinstance(parent_key.curve,ec.SECP256R1):
        raise ValueError("ES256 requires P-256 parent key")
    if len(entry.signature)!=64:
        raise ValueError("ES256 COSE signature must be 64-byte raw R||S")
    r=int.from_bytes(entry.signature[:32],"big")
    s=int.from_bytes(entry.signature[32:],"big")
    parent_key.verify(encode_dss_signature(r,s),sig_structure(entry,external_aad),ec.ECDSA(hashes.SHA256()))
    return entry
