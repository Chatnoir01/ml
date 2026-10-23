# Independent source-receipt auditor for TPM 96-session experiment

**Purpose:** audit the frozen 96-trial report produced by PR #150 *without*
altering a single seed, model parameter, attack implementation, selected
comparison or preregistered statistical endpoint.

This is a **separate stacked PR** so the original protocol and source-run
commit `4e4fe773dd9927e17a880f6302df415875a1c841` stay unchanged
while its GitHub Actions jobs run. The auditor is written without examining
any results of the new 96-trial campaign.

## What it checks independently

- Fixed three scales, **32 trial indices each**, plan SHA-256
  `6d282d9130f03e41204607af690c50501afec816d5820639c2eeba2178d69569`,
  and the exact TPM protocol SHA-256 recomputed from each scale's K/N/L,
  max steps, seed and update rule.
- Exact expected JSON schemas both at document and per-trial levels;
  reject extra fields such as raw weights, keys or hidden-state arrays.
- For each trial, legitimate synchronization status and step; all four
  work counters must be nonnegative and per-pair attacker forward
  evaluations equal. An unsynchronized trial must expose **null** attacker
  success and time, not a fabricated success or failure.
- Independently recompute all sums from raw booleans: synchronized/censored,
  cooperative successes, geometric successes, paired both/only/neither.
- Independently recompute median legitimate synchronization steps, Wilson
  95% intervals and exact two-sided McNemar p-values.
- Apply **Holm adjustment over the full three-scale multiplicity family**,
  including p=1 for any fully censored scale, so the family cannot shrink
  post hoc.
- Reject doctored aggregate statistics, confidence intervals, p-values,
  trial order, missing rows or wrong research-only flags.

## Independence constraints

The verifier uses `hashlib`, `math`, `json`, `statistics` and
frozen literal scale configuration. It does **not** import/run the attacker
algorithms or `run_multiscale()` to regenerate a supposedly matching
answer; it works only on the saved JSON output. The tests use a clearly
labelled **synthetic** 96-row fixture and deliberate corrupted variants,
NOT the reserved security experiment. No new sample is collected here.

## Validation and follow-up

Run synthetic audit regression:
```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_tpm_multiscale_audit.py
```

When the **original** PR #150 code has finished the 96-trial source run,
download its archived raw `tpm_multiscale_96_report.json` (not a manually
transcribed summary) and audit it with:

```bash
python scripts/audit_tpm_multiscale_report.py tpm_multiscale_96_report.json > tpm_multiscale_96_audited.json
```

Check the report's artifact digest and exact commit SHA before publishing
interpretation. A green audit confirms internal consistency of a simulation
report, **not cryptographic security**, equivalent adversarial computing
resources, quality of outside attacker implementations or statistical
extrapolation beyond the three toy sizes.
