from __future__ import annotations
import hashlib
import pytest

from secure_core_mobile.pvm_attestation import PvmAttestationStatement
from secure_core_mobile.pvm_verifier import PvmVerificationResult
from secure_core_mobile.verified_boundary import boundary_from_verified_attestation


def _statement(auth=True, monotonic=True):
    return PvmAttestationStatement(
        schema_version=1, boundary_id="pvm-1", measurement_sha256="a"*64,
        challenge_sha256=hashlib.sha256(b"c").hexdigest(),
        public_key_sha256="b"*64,
        authorization_state_inside_boundary=auth,
        monotonic_state_inside_boundary=monotonic,
    )


def test_unverified_result_cannot_assert_isolation():
    result = PvmVerificationResult(True, True, True, False, "chain-not-verified")
    with pytest.raises(ValueError, match="unverified"):
        boundary_from_verified_attestation(
            statement=_statement(), result=result, evidence_bytes=b"evidence"
        )


def test_forged_fully_verified_result_cannot_create_qualifying_boundary():
    # Anyone can instantiate these four True flags without a native verifier.
    result = PvmVerificationResult(True, True, True, True, "verified")
    with pytest.raises(ValueError, match="authoritative Android pVM"):
        boundary_from_verified_attestation(
            statement=_statement(), result=result, evidence_bytes=b"evidence"
        )


@pytest.mark.parametrize("auth,monotonic", [(False, True), (True, False)])
def test_required_state_must_live_inside_boundary(auth, monotonic):
    result = PvmVerificationResult(True, True, True, True, "verified")
    with pytest.raises(ValueError):
        boundary_from_verified_attestation(
            statement=_statement(auth, monotonic), result=result, evidence_bytes=b"e"
        )
