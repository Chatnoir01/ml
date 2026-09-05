# Phase 2A — Fresh-panel Neural Oracle Qualification Result

## Verdict

**`phase2a_oracle_not_qualified`**

Phase 2A does **not** qualify the Neural Oracle for evolutionary feedback. No neural score may influence GA selection on the basis of this experiment. Phase 2B GA↔NN co-evolution remains blocked.

## Frozen execution provenance

- scientific execution SHA: `357efc8ee7ea2151ea66d91e1bf78cb85240448e`
- GitHub Actions run: `33994488944`
- aggregate artifact ID: `9977640569`
- aggregate artifact ZIP SHA-256: `6b99bc5310a8852e69a55e8d1331f1c68df2697a2a06e20400250e7f8ca9a44a`
- aggregate payload SHA-256: `9b7d162fdc6f6df38fd394e6d93634caf569310b1707c9b35dfdde68ce5b746f`
- frozen panel digest SHA-256: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- total neural trainings: `120`
- neural evolutionary pressure during Phase 2A: `false`

## Qualification checks

| Check | Result |
| --- | --- |
| Oracle heterogeneity | PASS |
| Oracle score range | PASS |
| Oracle signal | PASS |
| Challenger heterogeneity | PASS |
| Challenger score range | PASS |
| Challenger signal | PASS |
| Panel revalidated | PASS |
| Training count exact | PASS |
| Deterministic receipts | PASS |
| **Oracle/challenger rank replication** | **FAIL** |

All preregistered checks were required. Because rank replication failed, the overall verdict is negative.

## Main numerical result

### Oracle side

- heterogeneity permutation p-value: `0.00009999000099990002`
- candidate score range: `0.10825880815843852`
- signal condition: `true`

Candidate mean advantages, in frozen panel order:

1. seed 2609 — `0.40033027261231774`
2. seed 2657 — `0.2920714644538792`
3. seed 2647 — `0.35662528329435406`
4. seed 2633 — `0.31362989570096755`
5. seed 2663 — `0.35631687389419275`
6. seed 2621 — `0.3661389848243612`

### Challenger side

- heterogeneity permutation p-value: `0.0024997500249975004`
- candidate score range: `0.04123046414466329`
- signal condition: `true`

Candidate mean advantages, in frozen panel order:

1. seed 2609 — `0.030563264963370418`
2. seed 2657 — `0.034279154026414585`
3. seed 2647 — `0.029412744465507144`
4. seed 2633 — `0.03395471364184033`
5. seed 2663 — `0.029093701766789003`
6. seed 2621 — `0.0703241659114523`

### Cross-architecture replication

- Oracle/challenger Spearman rank correlation: **`-0.08571428571428572`**
- preregistered rank-replication check: **FAIL**

The two architectures each detect statistically significant between-S-box heterogeneity, but they do not reproduce the same candidate ordering. Therefore the current neural score is not sufficiently architecture-stable to be used as an evolutionary objective.

## Interpretation

This is a scientifically informative negative result, not evidence that the neural signal is absent. The data show two simultaneous facts:

1. **S-box-specific neural heterogeneity exists under both frozen neural regimes.** Both sides pass their preregistered heterogeneity, range, and signal checks.
2. **The ordering is not architecture-stable.** The near-zero/slightly negative Spearman correlation means the current oracle and challenger disagree on which classically matched S-boxes are relatively easier or harder for the neural distinguisher.

Consequently, Phase 2A supports further controlled study of the source of the neural heterogeneity, but it does not justify feeding a neural score back into the GA.

## What this does not establish

This result does not establish neural resistance, physical side-channel resistance, cryptographic security, superiority to AES or any deployed primitive, or successful GA↔NN co-evolution.

## Frozen next-step rule

Do not retune Phase 2A in place. Any follow-up must be a separately preregistered experiment with fresh design decisions and, where applicable, fresh holdout data/seeds. Phase 2B remains locked unless a future qualification experiment establishes a stable neural objective under its own frozen acceptance criteria.
