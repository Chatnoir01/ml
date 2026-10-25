# Secure Core: do not promote synthetic Android pVM evidence (2026-10-25)

**Status: fail-closed development security gate. Not a hardware attestation, native Android implementation, or cryptographic security result.**

## Observed weakness

Two public, caller-constructible Python objects were previously sufficient to create a seemingly qualified boundary:

1. `PvmVerificationResult(True, True, True, True, "verified")` handed to `boundary_from_verified_attestation()`, with arbitrary statement and nonempty evidence bytes, produced `BoundaryEvidence(ANDROID_PVM, isolated_from_host=True, ...)`.
2. `BoundaryEvidence(ANDROID_PVM, True/True/True, arbitrary SHA-256)` itself made `qualifies_for_hostile_host_experiment` true. Callers could combine this with four freely supplied `SecurityCapability` flags to make `hostile_host_ready` true and generate a misleading "hostile-host-isolated-boundary" software receipt.

These are **claim-provenance / evidence-validation bugs**, not demonstrated extraction of real cryptographic keys or a vulnerability in Android.

## Temporary fail-closed repair

- `boundary_from_verified_attestation()` cannot promote a boolean `PvmVerificationResult` to verified Android isolation. It refuses with `authoritative Android pVM boundary attestation not provisioned`. Its existing negative validation paths remain.
- `BoundaryEvidence.qualifies_for_hostile_host_experiment` always returns False while the native trustworthy issuer is unavailable. A self-authored dataclass or SHA digest can never stand in for remote attestation.
- `SecurityCapability.hostile_host_ready`, `HostileHostProtocol.authorize_execution` and hostile-campaign receipt hardware qualification now stay false for such synthetic records.
- New regression tests cover constructed all-True PvmVerificationResult, fabricated ANDROID_PVM boundaries, all-True SecurityCapability flags, and a synthetically PASSing campaign whose receipt must remain development-only.

The repair intentionally sacrifices the previous synthetic "qualified" positive path. It preserves ordinary development campaign behavioral results and does not rewrite frozen experiments or native Android code.

## Future integration gate (separate project)

A non-Python-attacker-controlled authority must verify challenge freshness, Android/AVF/RKP chain and pinned roots, VM measurement, relevant isolated policy state and monotonic/rollback protection. It must issue a result that cannot be fabricated by constructing a Python dataclass or passing a caller-controlled digest. Only then should a *new, reviewed* boundary promotion API restore true qualification. A green CI run of synthetic tests is not a substitute for real device evidence.

## Verification commands

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/secure_core_mobile/test_verified_boundary.py tests/secure_core_mobile/test_security_gate_manifest.py tests/secure_core_mobile/test_hostile_boundary_self_attestation.py
python -m pytest -q tests/secure_core_mobile
```

Exact-head GitHub Actions CI must pass before merge. This work is stacked above the separate hostile-campaign deduplication fix. No automatic merge, no product deployment.
