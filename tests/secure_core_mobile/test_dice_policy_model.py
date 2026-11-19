import pytest
from secure_core_mobile.dice_policy_model import *
from secure_core_mobile.microdroid_dice_policy import *


def test_exact_authority_and_mode_with_ge_security_version():
    p=DiceEntryExpectation(b"a"*64,1,7).node_policy()
    p.verify({"authority_hash":b"a"*64,"mode":1,"security_version":8})
    with pytest.raises(ValueError,match="rollback"):
        p.verify({"authority_hash":b"a"*64,"mode":1,"security_version":6})
    with pytest.raises(ValueError,match="exact-match"):
        p.verify({"authority_hash":b"x"*64,"mode":1,"security_version":8})


def test_optional_security_version_matches_aosp_missing_ignore_semantics():
    DiceEntryExpectation(b"a"*64,1,7).node_policy().verify(
        {"authority_hash":b"a"*64,"mode":1}
    )


def test_policy_rejects_chain_length_change():
    policy=DicePolicyV1((DiceEntryExpectation(b"a"*64,1,1).node_policy(),))
    with pytest.raises(ValueError,match="size"):
        policy.verify(())


def test_payload_subcomponent_blocks_downgrade_and_authority_swap():
    p=PayloadSubcomponentExpectation(b"p"*64,4)
    p.verify({"authority_hash":b"p"*64,"security_version":5})
    with pytest.raises(ValueError,match="rollback"):
        p.verify({"authority_hash":b"p"*64,"security_version":3})
    with pytest.raises(ValueError,match="exact-match"):
        p.verify({"authority_hash":b"x"*64,"security_version":5})
