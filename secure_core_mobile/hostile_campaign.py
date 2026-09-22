"""Frozen hostile-host campaign specification and evaluator.

This is a development campaign until executed across a genuinely isolated,
verified pVM boundary. It never upgrades evidence by itself.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib
import json


class HostileScenario(str, Enum):
    UNKNOWN_HANDLE = "UNKNOWN_HANDLE"
    NONCE_REPLAY = "NONCE_REPLAY"
    POLICY_ROLLBACK = "POLICY_ROLLBACK"
    OPERATION_SUBSTITUTION = "OPERATION_SUBSTITUTION"
    HARDWARE_CAPABILITY_LIE = "HARDWARE_CAPABILITY_LIE"
    STATE_ROLLBACK = "STATE_ROLLBACK"
    RPC_REPLAY = "RPC_REPLAY"
    RPC_TAMPER = "RPC_TAMPER"


REQUIRED_SCENARIOS = tuple(HostileScenario)


@dataclass(frozen=True)
class ScenarioResult:
    scenario: HostileScenario
    denied: bool
    provider_reached: bool


@dataclass(frozen=True)
class HostileCampaign:
    protocol_version: int = 1
    frozen: bool = True

    @property
    def spec_sha256(self) -> str:
        body = json.dumps({
            "protocol_version": self.protocol_version,
            "frozen": self.frozen,
            "required_scenarios": [x.value for x in REQUIRED_SCENARIOS],
        }, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(body).hexdigest()

    def evaluate(self, results: tuple[ScenarioResult, ...]) -> bool:
        if not self.frozen or self.protocol_version != 1:
            return False
        by_name = {r.scenario: r for r in results}
        if set(by_name) != set(REQUIRED_SCENARIOS):
            return False
        return all(r.denied and not r.provider_reached for r in by_name.values())
