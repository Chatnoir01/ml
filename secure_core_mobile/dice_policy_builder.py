"""Build DICE policy constraints from an observed Android DICE-chain model.

Mirrors the AOSP builder rule: policy version and root public key are exact
matches; later nodes derive requested constraints from the observed chain.
This module consumes already-decoded nodes and does not claim DICE-chain CBOR
decoder compatibility.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .dice_policy_model import ConstraintType, MissingAction
from .dice_policy_wire import WireConstraint, WireConstraintType, WireNodeConstraints, WireDicePolicy


@dataclass(frozen=True)
class ConstraintSpec:
    kind: ConstraintType
    path: tuple[int, ...]
    missing: MissingAction = MissingAction.FAIL


def _lookup(node: Any, path: tuple[int, ...]) -> Any:
    cur=node
    for key in path:
        if not isinstance(cur,dict) or key not in cur:
            raise KeyError(path)
        cur=cur[key]
    return cur


def build_policy(*, version: int, root_public_key: bytes,
                 certificate_nodes: tuple[dict[int, Any], ...],
                 specs: tuple[ConstraintSpec, ...]) -> WireDicePolicy:
    if version != 1:
        raise ValueError("unsupported explicit-key DICE chain version")
    # AOSP policy builder exact-matches the first two chain nodes wholesale.
    nodes=[
        WireNodeConstraints((WireConstraint(WireConstraintType.EXACT_MATCH,(0,),version),)),
        WireNodeConstraints((WireConstraint(WireConstraintType.EXACT_MATCH,(0,),root_public_key),)),
    ]
    for node in certificate_nodes:
        constraints=[]
        for spec in specs:
            try:
                value=_lookup(node,spec.path)
            except KeyError:
                if spec.missing is MissingAction.IGNORE:
                    continue
                raise ValueError(f"DICE policy path missing: {spec.path}")
            wire_kind=(WireConstraintType.EXACT_MATCH if spec.kind is ConstraintType.EXACT_MATCH
                       else WireConstraintType.GREATER_OR_EQUAL)
            if wire_kind is WireConstraintType.GREATER_OR_EQUAL and (
                not isinstance(value,int) or isinstance(value,bool)
            ):
                raise ValueError("GreaterOrEqual DICE value must be integer")
            constraints.append(WireConstraint(wire_kind,spec.path,value))
        nodes.append(WireNodeConstraints(tuple(constraints)))
    return WireDicePolicy(tuple(nodes))
