# Phase 1N scientific execution authorization

AUTHORIZED_PHASE1N_SCIENTIFIC_RUN

This marker is created only after:

- public preregistration issues #43–#47;
- fresh seed quarantine;
- frozen `PHASE1N_PROTOCOL.md`;
- red-first contract evidence on commit `90effceccd1d13bf25dcd374a133790922592f3a`;
- red Phase 0 CI run `33977035554` failing because `adversarial_sbox.phase1n` did not yet exist;
- historical Phase 1 benchmark `33977035598` remaining green on the red contract commit;
- joint DDT+Walsh implementation;
- exact 340-evaluation ledger inherited and enforced for Phase 1N arms;
- green Python 3.10/3.11/3.12 CI run `33977172687`;
- green historical Phase 1 benchmark run `33977172616`;
- full PR #48 diff inspection with no mutation of historical GA/Pareto/CryptoShield or Phase-1M result semantics.

Engine/workflow SHA before this authorization marker: `9bf65cd566a72116ae50b254a1d74b726a86aafe`.

The commit containing this marker is the frozen Phase 1N scientific SHA. No Phase-1N parameter may be changed in response to development results. Confirmation seeds remain quarantined unless every preregistered development gate passes. Neural oracle remains blocked.
