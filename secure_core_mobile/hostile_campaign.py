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
        """Fail closed on ambiguous, missing or forged development observations.

        A duplicate scenario must never overwrite a previous failed observation.
        In particular, Python's truthiness of 1/0 is *not* boolean evidence.
        This only validates software observations; it never proves pVM isolation.
        """
        if type(self.protocol_version) is not int or self.protocol_version != 1:
            return False
        if self.frozen is not True:
            return False
        if not isinstance(results, tuple) or len(results) != len(REQUIRED_SCENARIOS):
            return False

        seen: set[HostileScenario] = set()
        required = set(REQUIRED_SCENARIOS)
        for result in results:
            if type(result) is not ScenarioResult:
                return False
            if type(result.scenario) is not HostileScenario or result.scenario not in required:
                return False
            if result.scenario in seen:
                return False
            seen.add(result.scenario)
            if result.denied is not True or result.provider_reached is not False:
                return False
        return seen == required
