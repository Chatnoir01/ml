"""Software tests for standard GLOBAL DDT histogram EA-invariance criterion.

All synthetic test permutations below are unrelated to real Phase 2U research
selection; they are structural regression fixtures only.
"""
import random
from unittest.mock import patch

import pytest

from adversarial_sbox.phase2a_candidates import CANDIDATES
from adversarial_sbox.phase2u_affine_invariant import (
    global_differential_spectrum, certify_full_source_panel,
)
from adversarial_sbox.phase2u_panel import AdmissionRejected


def _rot8(x, k):
    return ((x << k) | (x >> (8-k))) & 0xff


def test_full_ddt_spectrum_counts_every_nonzero_input_difference():
    original=tuple(CANDIDATES[0]["sbox"])
    counts=global_differential_spectrum(original)
    assert len(counts)==257
    assert sum(counts)==255*256
    assert sum(counts[i] for i in range(9,257))==0
    assert counts[2]==20150
    assert counts[4]==4944
    assert counts[6]==762
    assert counts[8]==79


def test_spectrum_invariant_under_extended_affine_transform():
    original=tuple(CANDIDATES[0]["sbox"])
    # Invertible affine input/output maps AND an arbitrary linear output
    # correction L(x)=rotl8(x,2) XOR x: genuine extended affine relation.
    changed=tuple(
        _rot8(original[_rot8(x, 1)^0xA5],3)
        ^ _rot8(x,2) ^ x ^ 0xC3
        for x in range(256)
    )
    assert len(set(changed))==256
    assert changed!=original
    assert global_differential_spectrum(changed)==global_differential_spectrum(original)


def test_historical_six_have_different_global_spectra():
    sig=[global_differential_spectrum(c["sbox"]) for c in CANDIDATES]
    assert len(sig)==len(set(sig))==6


def test_invalid_permutation_rejected_before_ddt_analysis():
    with pytest.raises(AdmissionRejected,match="bijective"):
        global_differential_spectrum([0]*256)
    with pytest.raises(AdmissionRejected,match="bijective"):
        global_differential_spectrum(list(range(255)))
    with pytest.raises(AdmissionRejected,match="bijective"):
        global_differential_spectrum([True]+list(range(1,256)))


def _synthetic_populations():
    # Deterministic, NOT the actual research panel; monkeypatching admission
    # here is only a deliberate unit-test fixture to exercise the certificate.
    result=[]
    for seed in range(20):
        boxes=list(range(256))
        random.Random(98765+seed).shuffle(boxes)
        result.append(tuple(boxes))
    return result


def test_distinct_synthetic_spectra_produce_certificate_without_neural_data():
    boxes=_synthetic_populations()
    fake_panel={
        "status":"PANEL_COMPLETE_NO_NEURAL_OUTCOMES",
        "panel_receipt_sha256":"a"*64,
        "examined_seed_count":19,
        "selected_candidates":[
            {"seed":41003+i,"sbox":list(s)}
            for i,s in enumerate(boxes[8:])
        ],
    }
    with patch("adversarial_sbox.phase2u_affine_invariant.aggregate",return_value=fake_panel):
        with patch("adversarial_sbox.phase2u_affine_invariant.exclusion_history",return_value=tuple(boxes[:8])):
            certificate=certify_full_source_panel([{"synthetic":"NO REAL RECEIPTS"}])
    assert certificate["new_candidate_count"]==12
    assert certificate["distinct_spectrum_count"]==20
    assert certificate["new_neural_trainings"]==0
    assert certificate["certificate_sha256"]
    assert certificate["certifies"].startswith("ALL_20_")


def test_matching_synthetic_spectrum_proves_that_certificate_must_fail():
    boxes=_synthetic_populations()
    boxes[8]=tuple(_rot8(boxes[0][_rot8(x,1)^0x5A],2)
                    ^ _rot8(x,1) ^ 0x55 for x in range(256))
    fake_panel={
        "status":"PANEL_COMPLETE_NO_NEURAL_OUTCOMES",
        "panel_receipt_sha256":"a"*64,
        "examined_seed_count":19,
        "selected_candidates":[
            {"seed":41003+i,"sbox":list(s)}
            for i,s in enumerate(boxes[8:])
        ],
    }
    with patch("adversarial_sbox.phase2u_affine_invariant.aggregate",return_value=fake_panel):
        with patch("adversarial_sbox.phase2u_affine_invariant.exclusion_history",return_value=tuple(boxes[:8])):
            with pytest.raises(AdmissionRejected,match="EA-family"):
                certify_full_source_panel([{"synthetic":"NO REAL RECEIPTS"}])


def test_incomplete_panel_never_receives_affine_certificate():
    with patch("adversarial_sbox.phase2u_affine_invariant.aggregate",return_value={
        "status":"SOURCE_PREFIX_PARTIAL_DO_NOT_PREDICT",
    }):
        with pytest.raises(AdmissionRejected,match="incomplete"):
            certify_full_source_panel([])
