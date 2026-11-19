from secure_core_mobile.explicit_dice_chain import canonical_cose_key, explicit_key_chain


def test_aosp_root_key_canonicalization_golden_vector():
    # AOSP libsecretkeeper_client::dice::root_key_deterministic_encoding
    root={"a":1,3:-7,1234:1,1:1}
    assert canonical_cose_key(root).hex()=="a4010103261904d201616101"
    assert explicit_key_chain(root).hex()=="82014ca4010103261904d201616101"


def test_root_map_input_order_cannot_change_explicit_chain():
    a={1:1,3:-7,1234:1,"a":1}
    b={"a":1,1234:1,3:-7,1:1}
    assert explicit_key_chain(a)==explicit_key_chain(b)
