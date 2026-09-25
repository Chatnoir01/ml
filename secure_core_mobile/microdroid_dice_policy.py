"""Microdroid Secretkeeper policy profile derived from AOSP updatable_vm rules."""
from __future__ import annotations
from dataclasses import dataclass
from .dice_policy_model import Constraint, ConstraintType, MissingAction, NodePolicy


@dataclass(frozen=True)
class DiceEntryExpectation:
    authority_hash: bytes
    mode: int
    minimum_security_version: int

    def node_policy(self) -> NodePolicy:
        return NodePolicy((
            Constraint(ConstraintType.EXACT_MATCH, ("authority_hash",), self.authority_hash),
            Constraint(ConstraintType.EXACT_MATCH, ("mode",), self.mode),
            Constraint(ConstraintType.GREATER_OR_EQUAL, ("security_version",),
                       self.minimum_security_version, MissingAction.IGNORE),
        ))


@dataclass(frozen=True)
class PayloadSubcomponentExpectation:
    authority_hash: bytes
    minimum_security_version: int

    def verify(self, component: dict) -> None:
        NodePolicy((
            Constraint(ConstraintType.EXACT_MATCH, ("authority_hash",), self.authority_hash),
            Constraint(ConstraintType.GREATER_OR_EQUAL, ("security_version",),
                       self.minimum_security_version),
        )).verify(component)
