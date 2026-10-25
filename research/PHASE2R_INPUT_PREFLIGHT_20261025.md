# Phase 2R — pinned input-generation invariance preflight

**Status: engineering preflight ONLY. No scientific training authorized or performed.**

## Why this addition exists

Phase 2G's archived checkpoint-0 model-state receipts matched between A/F for 5/9 evolution seeds and differed for 4/9. Identical declared seeds/curriculum are not enough to establish identical **bytes** of datasets or initial model weights. Phase 2H cannot infer a causal explanation for those historic mismatches from model-state hashes alone.

The existing Phase 2R contract (PR #131) already pins a new 20-S-Box synthetic curriculum, an exact data serializer and an audit of *future* receipts. This work adds a narrow executable preflight against the **actual Phase 2G data generator**, without running the trainer.

## Executed logic

- Verify actual committed synthetic fixture bytes through `load_phase2r_fixture()`.
- For a registered input difference and replicate T seed, call `build_shared_training_splits` three times in a single process:
  1. pinned curriculum;
  2. identical curriculum again;
  3. same candidates in reverse list order.
- Strictly require 5,600 training + 1,200 validation + 1,200 test samples on each invocation.
- Hash the *actual generated ciphertext-pair bytes*, not objects' reprs, using the frozen `phase2r_serialization.hash_pair_split` wire format.
- Fail closed if any repeated or reversed-input hash differs.
- Emit only SHA-256 hashes, seeded cell identity, safe split sizes, the exact pinned fixture digest and explicit scientific non-claims.
- A dedicated CI job also compares **two independent Python processes** executing the same single-cell preflight, with environment/host fixed within one CI job.

## Local, training-free check

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_phase2r_input_preflight.py
python -c 'from adversarial_sbox.phase2r_input_preflight import preflight_phase2r_input_cell as probe; print(probe(difference=1, replicate=0))'
```

The script runs a single registered input cell (three equivalent generations). It does **not** run 16 neural training cells, Phase 2G evolution, Phase 2H causal tests, Phase 2R's prospective training experiment or held-out validation.

## Exact limitations

- A deterministic input dataset does **not** imply deterministic model initialization/training or equal runtime environments. More than one process on one CI runner is also not independent hardware replication.
- This preflight uses the new synthetic Phase 2R fixture, **not** the old Phase 2G population; it cannot retrospectively reconstruct the historical four mismatches.
- The test does not establish cryptographic security, an improvement to S-Boxes, or success of GA/NN coevolution.
- No output from this probe can authorize Phase 2I. The full Phase 2R scientific execution remains locked behind the separate frozen protocol, environment and source evidence, and explicit prospective authorization.
- Do not alter any historic evidence, seeds or held-out data to make this preflight pass.

## Next hard gate

Independently instrument dataset hashes **and model-initialization/model-state hashes**, freeze the runtime dependencies and fresh run identities, then execute the already-defined four-run comparison only after a distinct scientific execution marker is approved. If input bytes differ, stop and diagnose dataset generation. If inputs and initialization match but model bytes diverge, investigate nondeterministic numerical execution without attributing it to adaptive learning.
