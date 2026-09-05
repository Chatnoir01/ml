# Phase 2A Neural Oracle Qualification — Execution Authorization

AUTHORIZED_PHASE2A_NEURAL_QUALIFICATION

This marker authorizes only the preregistered Phase-2A Neural Oracle qualification experiment.

Frozen classical panel provenance:
- panel reconstruction workflow run: `33985900321`
- panel reconstruction scientific SHA: `b671c2954c79a45c83899d6d779a3985ddd01c26`
- panel artifact ID: `9975299401`
- panel artifact SHA-256: `bf9ec26b4e030e6a58f99fbea9aa9c2ca732683391200484e380c8a89df9fb3e`
- panel digest SHA-256: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- panel size: `6`
- deterministic replay: `true`
- independent classical revalidation: `true`
- neural training during panel reconstruction: `false`

The exact panel is committed in `src/adversarial_sbox/phase2a_candidates.py` and protected by `tests/test_phase2a_candidates.py`.

Scientific design remains frozen as preregistered in `research/PHASE2A_PROTOCOL.md`:
- 4 frozen neural cells;
- 30 trainings per cell;
- 120 trainings total;
- oracle: 4-round bit ReLU MLP at differences `0x00000001` and `0x00000100`;
- challenger: 5-round byte tanh MLP at differences `0x00010000` and `0x01000000`;
- dataset seeds and model seeds remain frozen;
- 10,000 blocked-permutation repetitions;
- all qualification checks must pass for `phase2a_oracle_qualified`.

No neural score may influence GA selection in Phase 2A. A PASS qualifies the oracle only for a separately preregistered Phase 2B experiment; it does not prove cryptographic security, physical side-channel resistance, or superiority to AES.
