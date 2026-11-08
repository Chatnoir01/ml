# TPM Lab v1 — mutual neural synchronization with passive attackers

**Status:** classical, tiny-parameter, exploratory *research only*. Do not use
as key exchange, a secure secret generator or part of CryptoWall. Results
are not evidence of confidentiality.

## Scientific basis and model
- Rosen-Zvi et al., *Mutual learning in a tree parity machine and its
  application to cryptography*, Phys. Rev. E **66** (2002), 066135,
  https://doi.org/10.1103/PhysRevE.66.066135
- Ruttor et al., *Genetic attack on neural cryptography*, Phys. Rev. E
  **73** (2006), 036121.
- Shacham et al., *Cooperating attackers in neural cryptography*, Phys. Rev.
  E **69** (2004), 066137; group attacks are **NOT** implemented here.

This is **not** Abadi–Andersen's differentiable Alice/Bob/Eve experiment:
a discrete tree parity machine (TPM) is an integer-weight synchronization
model, not learned encryption of ordinary plaintext.

## Locked development pilot

- `K=3` hidden units; `N=8` inputs per hidden unit; integer weights in
  `[-L,L]` for `L=2`.
- Independent random uniform `x_{kn} ∈ {-1,+1}` shared publicly each step;
  hidden output `sigma_k=sign(sum_n w_kn x_kn)` (tie sign +1);
  public output `tau=product_k sigma_k`.
- Only when Alice's and Bob's public parity bits agree do both update the
  hidden units with `sigma_k == tau`: `w_kn <- clip(w_kn + tau*x_kn,-L,L)`.
  This is a specified Hebbian update, not a learned post-hoc rule.
- Three passive attacker models see exactly the same public input and
  Alice/Bob public parity outputs; they do **not** receive private weights:
  1. **Naive**: updates only when its own public parity agrees.
  2. **Geometric**: if its parity disagrees, flips the hidden unit with
     smallest absolute local field, then updates with target parity.
  3. **Random-flip control**: if its parity disagrees, flips a uniformly
     random hidden unit, then updates with target parity.
- At exact private-weight equality Alice/Bob, the **simulation only**
  compares each Eve's current private weights against Alice's. That is
  scientific instrumentation and **not a practical public detection rule**.
  Trials not synchronized before `max_steps` are *censored*, not attacker
  failures.
- Exactly 8 pilot trials, master seed `782023`, independent public-state and
  model RNG streams per trial, `max_steps=8000`. No attacker training after
  convergence and no cherry-picking which seeds to report.
- Versioned protocol SHA-256:
  `9019f6328bb619a8a0ffe2dc22d4271220973d37ea03ea79bc9c5868e90f08c4`.

The simulation exports only aggregate outcomes and public run metadata,
**never raw private weight vectors or a key**. Python `random.Random` is
deterministic for experiments and is **NOT a cryptographic RNG**.

## Locally observed, non-confirmatory pilot (23 October 2026)

For the protocol above, the locally run program reported:
- Alice/Bob synchronized: **8/8**; median 83.5 public-input rounds to equality.
- At legitimate synchronization, naive Eve exactly matched in **0/8**,
  geometric Eve in **4/8**, and random-flip Eve in **1/8** trials.

This is **tiny, exploratory, and low-entropy by design**. The numerical
comparison depends on the tested update convention, parameters and
attacker implementations. The `4/8` geometric matches strongly illustrate
why an unsuccessful naive attacker cannot justify a secure-key claim.
Do not extrapolate these ratios into a population-level security estimate.
An external cryptanalyst could recover weights without using any of these
specific models.

## Missing scientific and security gates

- Much larger preregistered independent seed study, intervals on
  synchronization/attack success and non-synchronization outcomes.
- Realistic attacker ensembles: majority flipping, geometric ensembles,
  genetic attacks, optimised CPU/GPU search, chosen public inputs and
  malicious channel participants, transcript replay and related attacks.
- Channel authentication and transcript integrity are **absent**.
- Keys derived from these weights are **not** evaluated for entropy,
  unpredictable secrecy, or resistance to classical/quantum cryptanalysis.
- No entropy extractor, key confirmation, key erasure or key reuse policy.
- Public parity agreement does not demonstrate equality of private weights;
  the experiment uses a privileged equality oracle to record times.
- No formal indistinguishability security claim. This tool is unsuitable
  for user communications or encryption keys.
- No mobile, production CryptoWall, S-Box Phase 2G/H/R or FHE integration.

## Test workflow

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_tpm_lab.py
python scripts/run_tpm_lab.py --smoke
python scripts/run_tpm_lab.py
```

CI runs the small deterministic engineering regression and `--smoke` only.
All model and attacker outputs are interpretive metrics, not a security verdict.
