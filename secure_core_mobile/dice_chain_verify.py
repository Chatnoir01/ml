"""Cryptographic verifier for an ES256 Android DICE chain subset.

Each COSE_Sign1 entry is verified by the current parent key. The authenticated
payload must carry SUBJECT_PUBLIC_KEY as a COSE_Key byte string; that key then
becomes the verifier for the next entry.

This is chain authenticity under a supplied root key, not Android provenance.
"""
from __future__ import annotations
from dataclasses import dataclass
from cryptography.hazmat.primitives.asymmetric import ec

from .cose_sign1_payload import decode_one
from .cose_sign1_verify import verify_es256

SUBJECT_PUBLIC_KEY=-4670552
COSE_KTY=1
COSE_ALG=3
COSE_CRV=-1
COSE_X=-2
COSE_Y=-3
KTY_EC2=2
ALG_ES256=-7
CRV_P256=1


def p256_from_cose_key(encoded:bytes)->ec.EllipticCurvePublicKey:
    key=decode_one(encoded)
    if not isinstance(key,dict):
        raise ValueError("subject public key is not a COSE_Key map")
    if key.get(COSE_KTY)!=KTY_EC2 or key.get(COSE_ALG)!=ALG_ES256 or key.get(COSE_CRV)!=CRV_P256:
        raise ValueError("unsupported DICE subject COSE_Key profile")
    x,y=key.get(COSE_X),key.get(COSE_Y)
    if not isinstance(x,bytes) or not isinstance(y,bytes) or len(x)!=32 or len(y)!=32:
        raise ValueError("invalid P-256 COSE_Key coordinates")
    return ec.EllipticCurvePublicNumbers(
        int.from_bytes(x,"big"),int.from_bytes(y,"big"),ec.SECP256R1()
    ).public_key()


@dataclass(frozen=True)
class VerifiedDiceChain:
    entries:int
    leaf_public_key:ec.EllipticCurvePublicKey


def verify_chain(root_key:ec.EllipticCurvePublicKey,entries:tuple[bytes,...])->VerifiedDiceChain:
    if not entries:
        raise ValueError("DICE chain requires at least one certificate entry")
    parent=root_key
    for encoded in entries:
        entry=verify_es256(encoded,parent)
        payload=decode_one(entry.payload)
        if not isinstance(payload,dict) or SUBJECT_PUBLIC_KEY not in payload:
            raise ValueError("authenticated DICE payload lacks subject public key")
        subject=payload[SUBJECT_PUBLIC_KEY]
        if not isinstance(subject,bytes):
            raise ValueError("DICE subject public key must be encoded bstr")
        parent=p256_from_cose_key(subject)
    return VerifiedDiceChain(len(entries),parent)
