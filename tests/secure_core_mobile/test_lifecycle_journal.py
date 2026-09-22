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
