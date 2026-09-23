"""Strict CBOR/COSE_Sign1 payload extractor for Android DICE entries.

Matches AOSP dice_policy behavior: a DiceChainEntry is a COSE_Sign1 array and
its payload must be present and itself decode to one CBOR value.

This is structural parsing only. It deliberately does NOT verify the Sign1
signature; callers must not treat successful extraction as chain authenticity.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


class CborDecodeError(ValueError): pass


def _read_uint(data:bytes,pos:int,ai:int)->tuple[int,int]:
    if ai<24:return ai,pos
    sizes={24:1,25:2,26:4,27:8}
    if ai not in sizes: raise CborDecodeError("indefinite/reserved CBOR unsupported")
    n=sizes[ai]
    if pos+n>len(data): raise CborDecodeError("truncated CBOR integer")
    value=int.from_bytes(data[pos:pos+n],"big")
    if (ai==24 and value<24) or (ai==25 and value<=0xff) or (ai==26 and value<=0xffff) or (ai==27 and value<=0xffffffff):
        raise CborDecodeError("non-canonical CBOR integer/length")
    return value,pos+n


def _item(data:bytes,pos:int=0)->tuple[Any,int]:
    if pos>=len(data): raise CborDecodeError("truncated CBOR")
    initial=data[pos];pos+=1
    major,ai=initial>>5,initial&31
    n,pos=_read_uint(data,pos,ai)
    if major==0:return n,pos
    if major==1:return -1-n,pos
    if major in (2,3):
        if pos+n>len(data): raise CborDecodeError("truncated CBOR bytes/text")
        raw=data[pos:pos+n];pos+=n
        return (raw if major==2 else raw.decode("utf-8")),pos
    if major==4:
        out=[]
        for _ in range(n):
            v,pos=_item(data,pos);out.append(v)
        return out,pos
    if major==5:
        out={}
        for _ in range(n):
            k,pos=_item(data,pos);v,pos=_item(data,pos)
            if k in out: raise CborDecodeError("duplicate CBOR map key")
            out[k]=v
        return out,pos
    raise CborDecodeError("unsupported CBOR major type")


def decode_one(data:bytes)->Any:
    value,pos=_item(data,0)
    if pos!=len(data): raise CborDecodeError("trailing CBOR data")
    return value


@dataclass(frozen=True)
class CoseSign1Entry:
    protected: bytes
    unprotected: dict
    payload: bytes
    signature: bytes


def parse_cose_sign1(encoded:bytes)->CoseSign1Entry:
    value=decode_one(encoded)
    if not isinstance(value,list) or len(value)!=4:
        raise ValueError("DiceChainEntry is not COSE_Sign1 array")
    protected,unprotected,payload,signature=value
    if not isinstance(protected,bytes) or not isinstance(unprotected,dict) or not isinstance(signature,bytes):
        raise ValueError("invalid COSE_Sign1 field types")
    if payload is None or not isinstance(payload,bytes):
        raise ValueError("COSE_Sign1 payload missing/invalid")
    return CoseSign1Entry(protected,unprotected,payload,signature)


def payload_value_from_cose_sign1(encoded:bytes)->Any:
    return decode_one(parse_cose_sign1(encoded).payload)
