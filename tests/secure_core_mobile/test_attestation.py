from __future__ import annotations
import hashlib

from secure_core_mobile.attestation import (
    AttestationEvidence,
    AttestationVerifier,
    ChallengeStore,
)
from secure_core_mobile.attestation_service import AttestationService


def _evidence(challenge, *, key="scm_key", nonce_hash=None, chain=(b"cert",)):
    return AttestationEvidence(
        challenge_id=challenge.challenge_id,
        challenge_nonce_sha256=nonce_hash or hashlib.sha256(challenge.nonce.encode()).hexdigest(),
        key_handle=key,
        certificate_chain_der=chain,
    )


def test_attestation_challenge_is_single_use():
    store = ChallengeStore()
    challenge = store.issue(now=100, ttl_seconds=10)
    assert store.consume(challenge.challenge_id, now=101) == challenge
    assert store.consume(challenge.challenge_id, now=102) is None


def test_expired_challenge_is_rejected_and_burned():
    store = ChallengeStore()
    challenge = store.issue(now=100, ttl_seconds=10)
    assert store.consume(challenge.challenge_id, now=111) is None
    assert store.consume(challenge.challenge_id, now=105) is None


def test_wrong_nonce_binding_fails_closed():
    verifier = AttestationVerifier()
    store = ChallengeStore()
    challenge = store.issue(now=100)
    verdict = verifier.verify(
        evidence=_evidence(challenge, nonce_hash="0" * 64),
        challenge=challenge,
        expected_key_handle="scm_key",
    )
    assert verdict.verified is False
    assert verdict.reason == "challenge-nonce-mismatch"


def test_wrong_key_binding_fails_closed():
    verifier = AttestationVerifier()
    store = ChallengeStore()
    challenge = store.issue(now=100)
    verdict = verifier.verify(
        evidence=_evidence(challenge, key="scm_other"),
        challenge=challenge,
        expected_key_handle="scm_key",
    )
    assert verdict.verified is False
    assert verdict.reason == "key-handle-mismatch"


def test_missing_chain_fails_closed():
    verifier = AttestationVerifier()
    store = ChallengeStore()
    challenge = store.issue(now=100)
    verdict = verifier.verify(
        evidence=_evidence(challenge, chain=()),
        challenge=challenge,
        expected_key_handle="scm_key",
    )
    assert verdict.verified is False
    assert verdict.reason == "certificate-chain-missing"


def test_unimplemented_hardware_chain_can_never_verify():
    verifier = AttestationVerifier()
    store = ChallengeStore()
    challenge = store.issue(now=100)
    verdict = verifier.verify(
        evidence=_evidence(challenge),
        challenge=challenge,
        expected_key_handle="scm_key",
    )
    assert verdict.verified is False
    assert verdict.reason == "hardware-trust-chain-verification-not-implemented"


def test_service_replay_is_rejected_before_second_verification():
    store = ChallengeStore()
    service = AttestationService(store, AttestationVerifier())
    challenge = store.issue(now=100)
    evidence = _evidence(challenge)
    first = service.verify_once(evidence=evidence, expected_key_handle="scm_key", now=101)
    replay = service.verify_once(evidence=evidence, expected_key_handle="scm_key", now=102)
    assert first.verified is False
    assert replay.verified is False
    assert replay.reason == "unknown-expired-or-replayed-challenge"
