from secure_core_mobile.android_dice_labels import *
from secure_core_mobile.dice_policy_wire import *


def test_android_dice_labels_are_pinned_to_aosp_values():
    assert AUTHORITY_HASH == -4670549
    assert CONFIG_DESC == -4670548
    assert KEY_MODE == -4670551
    assert COMPONENT_NAME == -70002
    assert COMPONENT_VERSION == -70003
    assert SECURITY_VERSION == -70005


def test_wire_policy_uses_numeric_android_paths_deterministically():
    node=WireNodeConstraints((
        WireConstraint(WireConstraintType.EXACT_MATCH,(AUTHORITY_HASH,),b"a"*64),
        WireConstraint(WireConstraintType.EXACT_MATCH,(KEY_MODE,),1),
        WireConstraint(WireConstraintType.GREATER_OR_EQUAL,(CONFIG_DESC,SECURITY_VERSION),7),
    ))
    policy=WireDicePolicy((node,))
    encoded=policy.encode()
    assert encoded == policy.encode()
    assert encoded[0] == 0x82  # [version, one node]
    assert encoded[1] == 0x01


def test_negative_integer_label_encoding_is_canonical():
    c=WireConstraint(WireConstraintType.EXACT_MATCH,(SECURITY_VERSION,),5).encode()
    # -70005 => CBOR negative integer major type 1, uint32 argument.
    assert bytes.fromhex("3a00011174") in c
