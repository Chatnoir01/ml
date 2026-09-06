from __future__ import annotations

from adversarial_sbox.evolution import evaluate_classical
from adversarial_sbox.phase2a import CandidateRecord, panel_digest
from adversarial_sbox.phase2au_candidates import (
    CANDIDATES,
    ELIGIBLE_SOURCE_SEED_COUNT,
    PANEL_DIGEST_SHA256,
    PANEL_SOURCE_ARTIFACT_ID,
    PANEL_SOURCE_ARTIFACT_SHA256,
    PANEL_SOURCE_RUN_ID,
    PANEL_SOURCE_SHA,
    SOURCE_SEEDS,
)
from adversarial_sbox.provenance import fingerprint_sbox


EXPECTED_SELECTED = (
    (90601, "05e8930587f02e1ec5bd336c73b922f043608f9ed4880a9a7a1227e748b80c56"),
    (90631, "0daf8a624f4707f0dce88d25a98fe04dce27d6de308b3a9a231ea7ec9a341c8d"),
    (90703, "13abb2b0bebdb57fcf34721bffcdec5721430432e35ea8f6527a85f61d35058c"),
    (90709, "31e71cb0be701272e68fa144d982c6b8a5a3ee7112e344c2877d44f6da4187fe"),
    (90671, "779172947fe8c5248656d0b51e01acf767baa9c401f86c5d81f71420335ae9f4"),
    (90641, "82544761e93d4b73076ffe24d1e9e1de013c6bdf5824481beb90ee117cfda4bc"),
)


def test_phase2au_panel_provenance_is_frozen() -> None:
    assert PANEL_SOURCE_SHA == "760570a360f1c64bd74c9a67682d72562976d678"
    assert PANEL_SOURCE_RUN_ID == 34024740672
    assert PANEL_SOURCE_ARTIFACT_ID == 9986778300
    assert PANEL_SOURCE_ARTIFACT_SHA256 == (
        "6f68ba00d58a9a88edc23362fbcc8c178269451dab109623de63f556c9f70539"
    )
    assert SOURCE_SEEDS == (
        90601,
        90617,
        90631,
        90641,
        90647,
        90659,
        90671,
        90677,
        90679,
        90697,
        90703,
        90709,
    )
    assert ELIGIBLE_SOURCE_SEED_COUNT == 8


def test_phase2au_panel_has_exact_selected_order_and_fingerprints() -> None:
    assert len(CANDIDATES) == 6
    assert tuple((item["source_seed"], item["fingerprint"]) for item in CANDIDATES) == EXPECTED_SELECTED
    assert len({item["source_seed"] for item in CANDIDATES}) == 6
    assert len({item["fingerprint"] for item in CANDIDATES}) == 6


def test_phase2au_panel_full_permutations_and_classical_metrics_revalidate() -> None:
    records: list[CandidateRecord] = []
    for item in CANDIDATES:
        sbox = tuple(int(value) for value in item["sbox"])
        assert len(sbox) == 256
        assert sorted(sbox) == list(range(256))
        assert fingerprint_sbox(sbox) == item["fingerprint"]

        metrics = evaluate_classical(sbox)
        assert metrics.differential_uniformity == 8
        assert metrics.nonlinearity == 100
        assert metrics.max_linear_correlation == 56
        assert metrics.algebraic_degree == 7
        assert metrics.sac_score == item["sac_score"]
        assert abs(metrics.sac_score - 0.5) <= 0.05

        records.append(
            CandidateRecord(
                source_seed=int(item["source_seed"]),
                fingerprint=str(item["fingerprint"]),
                sbox=sbox,
                differential_uniformity=int(item["differential_uniformity"]),
                nonlinearity=int(item["nonlinearity"]),
                max_linear_correlation=int(item["max_linear_correlation"]),
                algebraic_degree=int(item["algebraic_degree"]),
                sac_score=float(item["sac_score"]),
            )
        )

    assert panel_digest(tuple(records)) == PANEL_DIGEST_SHA256
    assert PANEL_DIGEST_SHA256 == "4da3a134ac18cea77fd7dbea3af465a88986831548c58a3310f13bb18471d451"
