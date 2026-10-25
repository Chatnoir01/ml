# Secure Core — hostile campaign evidence-integrity hardening (2026-10-25)

**Scope:** experimental Python security-claim evidence gate. **No verified Android pVM, hardware roots, or cryptographic key-protection claim.**

## Identified weakness

`HostileCampaign.evaluate()` previously compressed the submitted scenario observations into a dictionary keyed by scenario. Repeated observations for the same scenario were silently overwritten. An attacker or a faulty collection process could place a failed observation first and a successful observation later, causing the failed result to disappear. With one valid final observation for each required scenario, the campaign could be classified as PASS despite containing a failure.

Additionally, the prior predicate used Python truthiness, so `denied=1` and `provider_reached=0` could pass without literal boolean evidence. Its protocol-version/frozen checks also accepted boolean/integer lookalikes.

## Repair

- Demand exactly eight observations, one per frozen scenario.
- Fail closed on duplicate/missing/unexpected scenario identifiers.
- Require exact `ScenarioResult` entries and genuine `HostileScenario` enum values.
- Demand literal `denied is True` and `provider_reached is False`; no integer/string stand-ins.
- Require strict protocol version 1 and `frozen is True`.
- Preserve existing `HostileCampaign.spec_sha256` and receipt layout to avoid changing frozen protocol identity.
- Add negative/positive tests, including a forged passing last duplicate and receipt `campaign_passed=False` checks.

## Invariant

**Any failed or ambiguous observed attack scenario must prevent a campaign PASS.** Results from simulation are still simulation-only; a passing software campaign may never manufacture native hardware trust.

## Verification

The existing `Secure Core Mobile CI` workflow runs `tests/secure_core_mobile` across Python 3.10/3.11/3.12 on PRs. `Phase 0 CI` also runs the full repository suite. Do not claim tests have passed before exact-HEAD CI completion.

## Deferred gaps

The claim promotion gate still requires verifier-issued evidence for `ADVERSARIALLY_TESTED`. This PR does **not** implement any Android device-based hostile-host experiment, attestation trust anchors, or rollback-resistant storage. Future real-device evidence must be collected independently and reviewed before any security claim promotion.
