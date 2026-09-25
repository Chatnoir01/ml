import pytest

from secure_core_mobile.lifecycle_journal import InMemoryLifecycleJournal


def test_incomplete_intent_is_visible_for_recovery():
    journal = InMemoryLifecycleJournal()
    journal.begin(operation="destroy", handle="h1")
    pending = journal.incomplete()
    assert len(pending) == 1
    assert pending[0].handle == "h1"
    assert journal.durable is False


def test_commit_closes_intent_and_chain_verifies():
    journal = InMemoryLifecycleJournal()
    txid = journal.begin(operation="destroy", handle="h1")
    journal.commit(txid, operation="destroy", handle="h1")
    assert journal.incomplete() == ()
    journal.verify_chain()


def test_commit_without_intent_is_rejected():
    journal = InMemoryLifecycleJournal()
    with pytest.raises(ValueError, match="exactly one matching intent"):
        journal.commit("missing", operation="destroy", handle="h1")


def test_commit_metadata_mismatch_is_rejected_and_intent_stays_pending():
    journal = InMemoryLifecycleJournal()
    txid = journal.begin(operation="destroy", handle="h1")
    with pytest.raises(ValueError, match="metadata mismatch"):
        journal.commit(txid, operation="rotate", handle="h1")
    pending = journal.incomplete()
    assert len(pending) == 1
    assert pending[0].txid == txid


def test_duplicate_commit_is_rejected():
    journal = InMemoryLifecycleJournal()
    txid = journal.begin(operation="destroy", handle="h1")
    journal.commit(txid, operation="destroy", handle="h1")
    with pytest.raises(ValueError, match="already committed"):
        journal.commit(txid, operation="destroy", handle="h1")
    journal.verify_chain()
