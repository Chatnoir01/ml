"""Minimal deterministic ExplicitKeyDiceCertChain conversion core.

AOSP format:
  [1, bstr(.cbor canonical COSE_Key), * DiceChainEntry]
This implementation accepts a decoded root COSE_Key map and opaque encoded
DiceChainEntry values. It does not verify COSE_Sign1 signatures.
"""
from __future__ import annotations
from typing import Mapping

VERSION=1


def _head(major:int,n:int)->bytes:
    if n<24:return bytes(((major<<5)|n,))
    if n<=0xff:return bytes(((major<<5)|24,n))
    if n<=0xffff:return bytes(((major<<5)|25,))+n.to_bytes(2,"big")
    if n<=0xffffffff:return bytes(((major<<5)|26,))+n.to_bytes(4,"big")
    raise ValueError("CBOR value too large")


def _int(v:int)->bytes:
    return _head(0,v) if v>=0 else _head(1,-1-v)


def _tstr(v:str)->bytes:
    b=v.encode();return _head(3,len(b))+b


def _scalar(v:object)->bytes:
    if isinstance(v,bool): raise TypeError("bool unsupported in minimal COSE_Key")
    if isinstance(v,int): return _int(v)
    if isinstance(v,str): return _tstr(v)
    if isinstance(v,bytes): return _head(2,len(v))+v
    raise TypeError("unsupported COSE_Key value")


def canonical_cose_key(key:Mapping[object,object])->bytes:
    encoded=[(_scalar(k),_scalar(v)) for k,v in key.items()]
    # RFC 8949 core deterministic map order: shorter encoded key first, then lexical.
    encoded.sort(key=lambda kv:(len(kv[0]),kv[0]))
    return _head(5,len(encoded))+b"".join(k+v for k,v in encoded)


def explicit_key_chain(root_key:Mapping[object,object], entries:tuple[bytes,...]=())->bytes:
    root=canonical_cose_key(root_key)
    items=[_int(VERSION),_head(2,len(root))+root,*entries]
    return _head(4,len(items))+b"".join(items)
