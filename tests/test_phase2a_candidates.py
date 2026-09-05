"""Red-first exact freeze contract for the Phase-2A neural panel."""

from adversarial_sbox.phase2a import CandidateRecord, panel_digest
from adversarial_sbox.phase2a_candidates import CANDIDATES, PANEL_DIGEST_SHA256
from adversarial_sbox.provenance import fingerprint_sbox

EXPECTED_PANEL_DIGEST = "35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30"
EXPECTED_ORDER = (
    (2609, "300769cec5fefe30060e5f04a2a976b728900ee2b121cbdb81e09ce5260b686b"),
    (2657, "47db19cbaf316bdfbd6cccaa2c96934122edb259758b301ac8e812c9a84e4c3b"),
    (2647, "72c4092c42e34efea6ee127355194ddfa254168759c67f9a4913a718c9830f9e"),
    (2633, "c2316833af9f4c0f73a8f44a2132d39ce414a14c4fd45553279e7fd87ae3f1e3"),
    (2663, "d6744195ad185ae528c68f6b40f658b94aee4682adf467a2d3154324140677c8"),
    (2621, "dfb70187d44c755a4fa4fa650602ce92d17e5ad1ef232a223780f1c5268a3df4"),
)


def _as_record(candidate):
    return CandidateRecord(
        source_seed=int(candidate["source_seed"]),
        fingerprint=str(candidate["fingerprint"]),
        sbox=tuple(int(value) for value in candidate["sbox"]),
        differential_uniformity=int(candidate["differential_uniformity"]),
        nonlinearity=int(candidate["nonlinearity"]),
        max_linear_correlation=int(candidate["max_linear_correlation"]),
        algebraic_degree=int(candidate["algebraic_degree"]),
        sac_score=float(candidate["sac_score"]),
    )


def test_phase2a_panel_is_exactly_the_reconstructed_frozen_panel():
    assert PANEL_DIGEST_SHA256 == EXPECTED_PANEL_DIGEST
    assert len(CANDIDATES) == 6
    assert tuple((int(c["source_seed"]), str(c["fingerprint"])) for c in CANDIDATES) == EXPECTED_ORDER

    records = tuple(_as_record(candidate) for candidate in CANDIDATES)
    assert panel_digest(records) == EXPECTED_PANEL_DIGEST

    for candidate in CANDIDATES:
        sbox = tuple(int(value) for value in candidate["sbox"])
        assert len(sbox) == 256
        assert set(sbox) == set(range(256))
        assert fingerprint_sbox(sbox) == candidate["fingerprint"]
        assert candidate["differential_uniformity"] == 8
        assert candidate["nonlinearity"] == 100
        assert candidate["max_linear_correlation"] == 56
        assert candidate["algebraic_degree"] == 7
        assert abs(float(candidate["sac_score"]) - 0.5) <= 0.05
