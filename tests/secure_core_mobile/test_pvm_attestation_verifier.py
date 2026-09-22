from __future__ import annotations
import hashlib
import pytest

from secure_core_mobile.pvm_attestation import (
    PvmAttestationStatement, PvmTrustStore, TrustedMeasurement,
)
from secure_core_mobile.pvm_verifier import PvmAttestationVerifier


def _statement(challenge=b"challenge", measurement="a" * 64):
    return PvmAttestationStatement(
        schema_version=1,
        boundary_id="pvm-1",
        measurement_sha256=measurement,
        challenge_sha256=hashlib.sha256(challenge).hexdigest(),
        public_key_sha256="b" * 64,
        authorization_state_inside_boundary=True,
        monotonic_state_inside_boundary=True,
    )


def test_unknown_measurement_fails_closed():
    verifier = PvmAttestationVerifier(PvmTrustStore(()))
    result = verifier.verify(
        statement=_statement(), challenge=b"challenge",
        signature=b"sig", certificate_chain=(b"cert",),
    )
    assert result.verified is False
    assert result.reason == "measurement-not-trusted"


def test_challenge_substitution_is_rejected():
    verifier = PvmAttestationVerifier(PvmTrustStore(()))
    with pytest.raises(ValueError, match="challenge"):
        verifier.verify(
            statement=_statement(), challenge=b"other",
            signature=b"sig", certificate_chain=(b"cert",),
        )


def test_trusted_measurement_is_not_enough_without_platform_verification():
    store = PvmTrustStore((TrustedMeasurement("a" * 64, "release-1"),))
    result = PvmAttestationVerifier(store).verify(
        statement=_statement(), challenge=b"challenge",
        signature=b"synthetic", certificate_chain=(b"synthetic-cert",),
    )
    assert result.statement_valid is True
    assert result.measurement_trusted is True
    assert result.signature_verified is False
    assert result.verified is False
    assert result.reason == "platform-signature-verification-not-implemented"


def test_missing_signature_evidence_is_explicit():
    store = PvmTrustStore((TrustedMeasurement("a" * 64, "release-1"),))
    result = PvmAttestationVerifier(store).verify(
        statement=_statement(), challenge=b"challenge",
        signature=b"", certificate_chain=(),
    )
    assert result.verified is False
    assert result.reason == "missing-platform-signature-evidence"


def test_malformed_digest_is_rejected():
    bad = _statement(measurement="not-a-sha")
    with pytest.raises(ValueError, match="measurement_sha256"):
        PvmAttestationVerifier(PvmTrustStore(())).verify(
            statement=bad, challenge=b"challenge",
            signature=b"x", certificate_chain=(b"x",),
        )
