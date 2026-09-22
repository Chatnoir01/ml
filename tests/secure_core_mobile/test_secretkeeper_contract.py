import pytest

from secure_core_mobile.secretkeeper import (
    DicePolicy, SecretkeeperCapability, SecretkeeperUnavailable,
)
from secure_core_mobile.secretkeeper_monotonic import SecretkeeperMonotonicRoot


def test_secretkeeper_unavailable_is_never_rollback_capable():
    backend = SecretkeeperUnavailable()
    assert backend.capability.qualifies_for_monotonic_security_state is False
    with pytest.raises(RuntimeError, match="not implemented"):
        backend.get(
            entry_id=b"i"*64,
            policy=DicePolicy("a"*64, ("b"*64,), (1,)),
        )


def test_partial_secretkeeper_capability_cannot_create_monotonic_root():
    cap = SecretkeeperCapability(True, True, True, False)
    with pytest.raises(ValueError, match="not sufficient"):
        SecretkeeperMonotonicRoot(capability=cap)


def test_full_capability_constructs_contract_but_io_stays_unimplemented():
    cap = SecretkeeperCapability(True, True, True, True)
    root = SecretkeeperMonotonicRoot(capability=cap)
    assert root.hardware_resistant is True
    assert root.boundary_owned is True
    with pytest.raises(RuntimeError, match="not implemented"):
        root.current()


def test_dice_policy_rejects_vector_mismatch():
    with pytest.raises(ValueError, match="vectors"):
        DicePolicy("a"*64, ("b"*64,), ()).validate()
