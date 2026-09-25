import pytest
from secure_core_mobile.android_dice_labels import AUTHORITY_HASH, CONFIG_DESC, SECURITY_VERSION
from secure_core_mobile.dice_policy_builder import build_policy, ConstraintSpec
from secure_core_mobile.dice_policy_model import ConstraintType, MissingAction


SPECS=(
    ConstraintSpec(ConstraintType.EXACT_MATCH,(AUTHORITY_HASH,)),
    ConstraintSpec(ConstraintType.GREATER_OR_EQUAL,(CONFIG_DESC,SECURITY_VERSION),MissingAction.IGNORE),
)


def test_builder_exact_matches_version_and_root_and_derives_later_values():
    node={AUTHORITY_HASH:b"a"*64,CONFIG_DESC:{SECURITY_VERSION:7}}
    p=build_policy(version=1,root_public_key=b"root",certificate_nodes=(node,),specs=SPECS)
    assert len(p.nodes)==3
    assert p.nodes[2].constraints[0].value==b"a"*64
    assert p.nodes[2].constraints[1].value==7
    assert p.encode()==p.encode()


def test_missing_ignore_omits_constraint_like_aosp_builder():
    node={AUTHORITY_HASH:b"a"*64}
    p=build_policy(version=1,root_public_key=b"root",certificate_nodes=(node,),specs=SPECS)
    assert len(p.nodes[2].constraints)==1


def test_missing_fail_and_noninteger_ge_are_rejected():
    fail=(ConstraintSpec(ConstraintType.EXACT_MATCH,(999,),MissingAction.FAIL),)
    with pytest.raises(ValueError,match="missing"):
        build_policy(version=1,root_public_key=b"r",certificate_nodes=({},),specs=fail)
    bad={CONFIG_DESC:{SECURITY_VERSION:b"7"}}
    specs=(ConstraintSpec(ConstraintType.GREATER_OR_EQUAL,(CONFIG_DESC,SECURITY_VERSION)),)
    with pytest.raises(ValueError,match="integer"):
        build_policy(version=1,root_public_key=b"r",certificate_nodes=(bad,),specs=specs)
