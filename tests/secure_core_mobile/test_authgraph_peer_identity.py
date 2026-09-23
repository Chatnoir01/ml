import pytest
from secure_core_mobile.authgraph_peer_identity import AuthGraphPeerIdentity, PolicyAuthorizationContext


def test_policy_identity_must_be_authgraph_peer_identity():
    peer=AuthGraphPeerIdentity.from_exchange(dice_chain=b"authenticated-dice-chain",session_id=b"sid")
    ctx=PolicyAuthorizationContext(peer,b"sid")
    ctx.validate(candidate_dice_chain=b"authenticated-dice-chain")
    assert len(peer.peer_identity_sha256)==64


def test_attacker_cannot_substitute_separate_dice_chain():
    peer=AuthGraphPeerIdentity.from_exchange(dice_chain=b"real-chain",session_id=b"sid")
    with pytest.raises(ValueError,match="substitution"):
        PolicyAuthorizationContext(peer,b"sid").validate(candidate_dice_chain=b"attacker-chain")


def test_identity_cannot_be_replayed_into_another_session():
    peer=AuthGraphPeerIdentity.from_exchange(dice_chain=b"real-chain",session_id=b"session-A")
    with pytest.raises(ValueError,match="session"):
        PolicyAuthorizationContext(peer,b"session-B").validate(candidate_dice_chain=b"real-chain")
