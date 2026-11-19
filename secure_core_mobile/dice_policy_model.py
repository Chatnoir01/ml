"""Executable subset of the AOSP DICE policy model used by Secretkeeper.

Models constraint semantics only; CBOR path labels are intentionally symbolic
until imported from authoritative Android CDDL/constants.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import Any


class ConstraintType(IntEnum):
    EXACT_MATCH = 1
    GREATER_OR_EQUAL = 2


class MissingAction(str, Enum):
    FAIL = "FAIL"
    IGNORE = "IGNORE"


@dataclass(frozen=True)
class Constraint:
    kind: ConstraintType
    path: tuple[str, ...]
    value: Any
    missing: MissingAction = MissingAction.FAIL

    def verify(self, node: dict[str, Any]) -> None:
        current: Any = node
        for part in self.path:
            if not isinstance(current, dict) or part not in current:
                if self.missing is MissingAction.IGNORE:
                    return
                raise ValueError(f"DICE policy value missing: {'.'.join(self.path)}")
            current = current[part]
        if self.kind is ConstraintType.EXACT_MATCH:
            if current != self.value:
                raise ValueError("DICE exact-match constraint failed")
            return
        if self.kind is ConstraintType.GREATER_OR_EQUAL:
            if not isinstance(current, int) or isinstance(current, bool):
                raise ValueError("DICE greater-or-equal requires integer")
            if current < self.value:
                raise ValueError("DICE security version rollback")
            return
        raise ValueError("unsupported DICE constraint")


@dataclass(frozen=True)
class NodePolicy:
    constraints: tuple[Constraint, ...]

    def verify(self, node: dict[str, Any]) -> None:
        for constraint in self.constraints:
            constraint.verify(node)


@dataclass(frozen=True)
class DicePolicyV1:
    nodes: tuple[NodePolicy, ...]
    version: int = 1

    def verify(self, chain: tuple[dict[str, Any], ...]) -> None:
        if self.version != 1:
            raise ValueError("unsupported DICE policy version")
        if len(chain) != len(self.nodes):
            raise ValueError("DICE chain size does not match policy")
        for policy, node in zip(self.nodes, chain):
            policy.verify(node)
