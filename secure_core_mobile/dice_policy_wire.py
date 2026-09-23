"""Deterministic CBOR encoder for the Secretkeeper DICE policy subset.

Wire shape follows AOSP DicePolicy CDDL:
  [version, + nodeConstraintList]
  nodeConstraintList = [* constraint]
  constraint = [type, path, value]
Path entries are Android DICE integer labels.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Union

Scalar = Union[int, bytes]


class WireConstraintType(IntEnum):
    EXACT_MATCH = 1
    GREATER_OR_EQUAL = 2


def _head(major:int,n:int)->bytes:
    if n < 24: return bytes(((major<<5)|n,))
    if n <= 0xff: return bytes(((major<<5)|24,n))
    if n <= 0xffff: return bytes(((major<<5)|25,))+n.to_bytes(2,"big")
    if n <= 0xffffffff: return bytes(((major<<5)|26,))+n.to_bytes(4,"big")
    return bytes(((major<<5)|27,))+n.to_bytes(8,"big")


def _int(v:int)->bytes:
    return _head(0,v) if v >= 0 else _head(1,-1-v)


def _bstr(v:bytes)->bytes: return _head(2,len(v))+v
def _array(items:list[bytes])->bytes: return _head(4,len(items))+b"".join(items)


def _scalar(v:Scalar)->bytes:
    if isinstance(v,bool): raise TypeError("bool is not a DICE policy scalar here")
    if isinstance(v,int): return _int(v)
    if isinstance(v,bytes): return _bstr(v)
    raise TypeError("unsupported DICE policy scalar")


@dataclass(frozen=True)
class WireConstraint:
    kind: WireConstraintType
    path: tuple[int,...]
    value: Scalar

    def encode(self)->bytes:
        return _array([_int(int(self.kind)),_array([_int(x) for x in self.path]),_scalar(self.value)])


@dataclass(frozen=True)
class WireNodeConstraints:
    constraints: tuple[WireConstraint,...]

    def encode(self)->bytes:
        return _array([x.encode() for x in self.constraints])


@dataclass(frozen=True)
class WireDicePolicy:
    nodes: tuple[WireNodeConstraints,...]
    version:int=1

    def encode(self)->bytes:
        if self.version != 1: raise ValueError("unsupported DICE policy version")
        return _array([_int(self.version),*[node.encode() for node in self.nodes]])
