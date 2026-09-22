from __future__ import annotations
import pytest

from secure_core_mobile.android_pvm import (
    AndroidPvmAdapter, PvmEvidenceBundle, PvmRuntimeState, probe_runtime,
)


def test_non_android_runtime_is_unavailable():
    probe = probe_runtime(platform="linux", avf_present=True)
    assert probe.state is PvmRuntimeState.UNAVAILABLE
    assert probe.reason == "non-android-runtime"


def test_android_without_avf_is_unavailable():
    probe = probe_runtime(platform="android", avf_present=False)
    assert probe.state is PvmRuntimeState.UNAVAILABLE


def test_avf_presence_is_not_trust_verification():
    probe = probe_runtime(platform="android", avf_present=True)
    assert probe.state is PvmRuntimeState.PRESENT_UNVERIFIED


def test_unverified_evidence_cannot_claim_host_isolation():
    evidence = AndroidPvmAdapter().ingest_unverified_evidence(PvmEvidenceBundle(
        boundary_id="pvm-1",
        measurement="measurement-1",
        authorization_state_inside_boundary=True,
        monotonic_state_inside_boundary=True,
        raw_evidence=b"synthetic-evidence",
    ))
    assert evidence.isolated_from_host is False
    assert evidence.qualifies_for_hostile_host_experiment is False
    assert len(evidence.evidence_sha256) == 64


def test_incomplete_evidence_fails_closed():
    with pytest.raises(ValueError, match="incomplete"):
        AndroidPvmAdapter().ingest_unverified_evidence(PvmEvidenceBundle(
            boundary_id="pvm-1",
            measurement="",
            authorization_state_inside_boundary=True,
            monotonic_state_inside_boundary=True,
            raw_evidence=b"x",
        ))
