"""RAVEN-007 crash-only local vote journal tests, NOT hardware/rollback security."""
from dataclasses import replace
from hashlib import sha256

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from research.raven_fork_evidence import CheckpointReceipt
from research.raven_quorum_model import (
    QuorumCertificate, Roster, verify_quorum_certificate,
    prove_witness_double_vote,
)
from research.raven_durable_witness_model import (
    DurableHonestWitness, FileVoteJournal, SimulatedCrash,
)
from research.raven_signed_model import Rejected


def digest(x: str) -> str:
    return sha256(x.encode()).hexdigest()


def rig(n=4, f=1):
    issuer=Ed25519PrivateKey.generate()
    keys={f"w{i}":Ed25519PrivateKey.generate() for i in range(n)}
    roster=Roster(
        issuer="issuer", namespace="test",
        compartment="c", genesis_commitment=digest("root"),
        issuer_key=issuer.public_key(),
        witnesses={name:key.public_key() for name,key in keys.items()},
        max_byzantine=f,
    )
    return issuer,keys,roster


def receipt(issuer: Ed25519PrivateKey, roster: Roster, name: str):
    unsigned=CheckpointReceipt(
        issuer=roster.issuer,namespace=roster.namespace,
        compartment=roster.compartment,
        parent_epoch=0,parent_commitment=roster.genesis_commitment,
        child_epoch=1,child_commitment=digest(name),
        child_policy_digest=digest("policy"),signature=b"",
    )
    return replace(unsigned,signature=issuer.sign(unsigned.message()))


def witness(tmp_path, keys, roster, who="w0"):
    return DurableHonestWitness(
        who,keys[who],roster,FileVoteJournal(tmp_path)
    )


def test_good_first_vote_and_same_vote_after_restart(tmp_path):
    issuer,keys,roster=rig()
    item=receipt(issuer,roster,"A")
    a=witness(tmp_path,keys,roster)
    first=a.endorse(item)
    assert a.endorse(item)==first
    b=witness(tmp_path,keys,roster)
    assert b.endorse(item)==first


def test_restarted_witness_refuses_conflicting_signed_receipt(tmp_path):
    issuer,keys,roster=rig()
    left=receipt(issuer,roster,"A")
    right=receipt(issuer,roster,"B")
    witness(tmp_path,keys,roster).endorse(left)
    with pytest.raises(Rejected,match="double vote"):
        witness(tmp_path,keys,roster).endorse(right)


@pytest.mark.parametrize("crashpoint",[
    "after_record_fsync","after_directory_fsync",
    "before_sign","after_sign",
])
def test_crash_after_intent_never_allows_other_child(tmp_path, crashpoint):
    issuer,keys,roster=rig()
    left,right=receipt(issuer,roster,"A"),receipt(issuer,roster,"B")
    first=witness(tmp_path,keys,roster)
    with pytest.raises(SimulatedCrash,match=crashpoint):
        first.endorse(left,crash_at=crashpoint)
    restarted=witness(tmp_path,keys,roster)
    with pytest.raises(Rejected,match="double vote"):
        restarted.endorse(right)
    assert restarted.endorse(left).receipt_hash==first.journal.commit_intent(
        roster,"w0",left
    )


def test_crash_before_create_creates_no_signature_or_intent(tmp_path):
    issuer,keys,roster=rig()
    old,new=receipt(issuer,roster,"A"),receipt(issuer,roster,"B")
    with pytest.raises(SimulatedCrash,match="before_create"):
        witness(tmp_path,keys,roster).endorse(old,crash_at="before_create")
    assert not list(tmp_path.iterdir())
    # No prior signature could be emitted: electing the other child
    # after a crash BEFORE the intent is not a safety violation.
    assert witness(tmp_path,keys,roster).endorse(new).receipt_hash


def test_crash_after_exclusive_open_fails_closed_instead_of_guessing(tmp_path):
    issuer,keys,roster=rig()
    old,new=receipt(issuer,roster,"A"),receipt(issuer,roster,"B")
    with pytest.raises(SimulatedCrash,match="after_open"):
        witness(tmp_path,keys,roster).endorse(old,crash_at="after_open")
    assert len(list(tmp_path.iterdir()))==1
    with pytest.raises(Rejected,match="damaged"):
        witness(tmp_path,keys,roster).endorse(old)
    with pytest.raises(Rejected):
        witness(tmp_path,keys,roster).endorse(new)


def test_safe_vote_still_constructs_valid_quorum_certificate(tmp_path):
    issuer,keys,roster=rig()
    item=receipt(issuer,roster,"A")
    votes=tuple(witness(tmp_path,keys,roster,who).endorse(item)
                for who in ("w0","w1","w2"))
    verify_quorum_certificate(QuorumCertificate(item,votes),roster)
    assert len(list(tmp_path.iterdir()))==3


def test_bad_signature_never_creates_vote_intent(tmp_path):
    issuer,keys,roster=rig()
    forged=receipt(Ed25519PrivateKey.generate(),roster,"A")
    with pytest.raises(Rejected,match="signature"):
        witness(tmp_path,keys,roster).endorse(forged)
    assert not list(tmp_path.iterdir())


def test_corrupt_journal_file_is_permanent_fail_closed_without_override(tmp_path):
    issuer,keys,roster=rig()
    item=receipt(issuer,roster,"A")
    witness(tmp_path,keys,roster).endorse(item)
    path=next(tmp_path.iterdir())
    path.write_text("{}")
    with pytest.raises(Rejected,match="corrupt"):
        witness(tmp_path,keys,roster).endorse(item)


def test_trusted_witness_directory_must_not_be_world_writable(tmp_path):
    issuer,keys,roster=rig()
    tmp_path.chmod(0o777)
    try:
        with pytest.raises(Rejected,match="group/world"):
            FileVoteJournal(tmp_path)
    finally:
        tmp_path.chmod(0o700)


def test_preexisting_symlink_voting_file_never_accepted(tmp_path):
    issuer,keys,roster=rig()
    obj=FileVoteJournal(tmp_path)
    item=receipt(issuer,roster,"A")
    identity=obj._identity(roster,"w0",item)
    path=obj._path(identity)
    target=tmp_path/"target.json"
    target.write_text("{}")
    path.symlink_to(target)
    with pytest.raises(Rejected):
        witness(tmp_path,keys,roster).endorse(item)


def test_stored_attestation_is_not_a_rollback_proof_negative_control(tmp_path):
    issuer,keys,roster=rig()
    left,right=receipt(issuer,roster,"A"),receipt(issuer,roster,"B")
    record=tmp_path/"current"; record.mkdir(mode=0o700)
    first=witness(record,keys,roster).endorse(left)
    # Deliberately restore an older EMPTY snapshot. Without an external
    # monotonic anchor, a host/backup operator can remove the vote journal.
    rolled_back=tmp_path/"old_snapshot";rolled_back.mkdir(mode=0o700)
    second=witness(rolled_back,keys,roster).endorse(right)
    prove_witness_double_vote(first,left,second,right,roster)
    # Hence no malicious rollback, HSM or distributed key-custody claim.


def test_unknown_crash_injection_phase_rejected(tmp_path):
    issuer,keys,roster=rig()
    with pytest.raises(ValueError,match="unknown"):
        witness(tmp_path,keys,roster).endorse(
            receipt(issuer,roster,"A"),crash_at="unregistered_stage"
        )
