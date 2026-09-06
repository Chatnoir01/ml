# Phase 2A-T — Frozen Result

## Official verdict

**`phase2at_depth4_peak_replicated`**

This file freezes the preregistered fresh-seed Phase 2A-T result exactly as produced by the scientific workflow. No in-place retuning is authorized from this result.

## Provenance

- public preregistration: issue #76
- execution lock: issue #77
- scientific SHA: `c10577d403daf13c7684f355501601a6783ca9a2`
- workflow run: `34024114413`
- exact neural trainings: `288`
- aggregate artifact ID: `9986498439`
- aggregate artifact ZIP SHA-256: `fa635855766977a950850f15ea3286f27bcae4506d59bbc02ad6cc128f276682`
- aggregate payload SHA-256: `f33bafec9269d90ff5c692b0e7ea322cbcca8116cffbc24da41d95082a395780`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- depths: `3, 4, 5`
- input differences at every depth: `0x00000001`, `0x00000100`
- paired replicates: `8`
- blocked heterogeneity permutations per depth: `10,000`
- neural evolutionary pressure: `false`

## Frozen prerequisite checks

All prerequisites passed:

- exact 288 training/provenance count: PASS
- frozen panel digest and classical revalidation: PASS
- deterministic receipts: PASS
- signal condition at all three depths: PASS
- neural evolutionary pressure absent: PASS

Therefore the preregistered profile rule is interpretable.

## Depth results

| Depth | Mean neural advantage M | Heterogeneity H | Permutation p | Candidate score range R | Signal |
|---|---:|---:|---:|---:|---|
| 3 | `0.988990860130687` | `1.3374308469582503e-06` | `0.4032596740325967` | `0.0032758821087554013` | PASS |
| 4 | `0.32838066594698173` | `0.0013404628952386607` | `9.999000099990002e-05` | `0.10658153113805419` | PASS |
| 5 | `0.04280126283748886` | `4.5547927157827505e-05` | `0.2873712628737126` | `0.01771316652683392` | PASS |

Descriptive adjacent candidate-rank Spearman correlations:

- `rho_34 = 0.37142857142857144`
- `rho_45 = 0.08571428571428572`

## Preregistered profile checks

All frozen directional criteria passed:

- `H4 > H3`: PASS
- `H4 > H5`: PASS
- `R4 > R3`: PASS
- `R4 > R5`: PASS
- `M3 > M4 > M5`: PASS
- depth-4 blocked heterogeneity `p < 0.05`: PASS

Therefore the frozen classification is:

**`phase2at_depth4_peak_replicated`**

It must not be upgraded after the fact into Neural Oracle qualification or GA↔NN authorization.

## Candidate mean neural advantages

Depth 3:
`[0.9897486328940039, 0.986662447406192, 0.9899383295149474, 0.9892882967761459, 0.9884502920901403, 0.9898571621026926]`

Depth 4:
`[0.3870684507628008, 0.2804869196247466, 0.34173487822206033, 0.2848737487965282, 0.3428633594512638, 0.3332566388244907]`

Depth 5:
`[0.03943737071487379, 0.04288509285659068, 0.036183758167326996, 0.035059022191327956, 0.0504701443766519, 0.052772188718161875]`

## Interpretation boundary

Phase 2A-T **replicates, on fresh neural seeds, the preregistered depth-profile hypothesis derived after Phase 2A-S**:

- at 3 rounds, the distinguisher is almost saturated for every candidate, so overall distinguishability is very high while between-S-box separation is tiny;
- at 4 rounds, S-box-specific separation is largest and blocked heterogeneity is strongly significant;
- at 5 rounds, overall neural advantage and between-S-box separation are both much smaller than at 4 rounds.

This supports the existence of a depth-4 peak **for this frozen ToySPN / panel / architecture / difference-family setup**. It does not establish a universal law of neural cryptanalysis, a causal mechanism, or a property of AES or any deployed cipher.

The descriptive candidate-rank correlations are not strong (`rho_34 ≈ 0.371`, `rho_45 ≈ 0.086`), so this experiment does not establish stable cross-depth candidate ranking and does not qualify a reusable Neural Oracle.

No neural score influenced evolution. No operational key recovery, AES/deployed-cipher weakness, physical side-channel resistance, production security, neural resistance, or successful GA↔NN co-evolution is claimed.

**Phase 2B GA↔NN remains blocked.** A Neural Oracle still requires a separately preregistered qualification/confirmation experiment designed around the now-replicated depth profile.
