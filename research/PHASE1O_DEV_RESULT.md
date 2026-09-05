# Phase 1O — multi-hotspot Walsh plateau development result

## Frozen verdict

`phase1o_dev_pass`

Phase 1O development passed every preregistered condition on the five fresh development seeds. This result authorizes only a separately preregistered confirmation experiment on the quarantined reserved seeds. It does **not** by itself turn Global Gate 1 green and it does **not** authorize Neural Oracle execution.

## Frozen provenance

- Phase 1N base merged on `main`: `ad3e7b0599727d0b0e7deb0db41fe338d46b67fa`
- Preregistration issues: #49 through #53
- Phase 1O branch: `research/phase1o-multihotspot-nl-repair`
- Seed registry commit: `09c7721b03c727a3840a90391698a27d81d04817`
- Frozen protocol commit: `411e2c3797fbab4f8c757e321cfb7d68a4103a58`
- Red-first contract commit: `91c37dd64951abdbaa472660d6032313ec119018`
- Red evidence: Phase 0 CI failed because `adversarial_sbox.phase1o` did not yet exist; historical Phase 1 benchmark remained green
- Phase 1O implementation commit: `952ca1dc73372fe952fdc1a51f36c0e16137c7e8`
- Locked development workflow commit: `f29149ada450becb9b15285546581128a5ad183c`
- Locked-head engineering evidence: Python 3.10/3.11/3.12 GREEN; historical Phase 1 benchmark GREEN
- Scientific execution SHA: `b3760f6a7973616fff9def3f7eb29df05fe5c149`
- Scientific workflow run: `33983168783`
- Aggregate artifact ID: `9974491042`
- Aggregate artifact digest: `sha256:dc600888121f40bce0f225660b5d445641aa8681c972cc39d92b4a214a712199`

## Frozen development seeds and budgets

Development seeds were exactly:

`2503, 2521, 2531, 2539, 2543`

For every seed:

- Arm A: exactly 340 unique full classical evaluations
- Arm B: exactly 340 unique full classical evaluations
- Arm C: exactly 340 unique full classical evaluations
- A/B/C used the same initial population digest within the seed
- fixed-seed scientific payload matched on deterministic rerun
- Arm A executed 320/320 multi-hotspot-guided proposals with 0 fallback proposals
- Neural Oracle was never executed

## Aggregate result

Frozen JOINT target:

- differential uniformity <= 8
- nonlinearity >= 100
- max absolute linear correlation <= 64
- algebraic degree >= 6

Aggregate comparison:

- seeds with >=1 JOINT candidate: Arm A **5/5**, Arm B **0/5**
- aggregate JOINT terminal candidates: Arm A **6**, Arm B **0**
- seeds with terminal DU <= 8: Arm A **5/5**, Arm B **3/5**
- paired best-DU wins / losses / ties for Arm A: **2 / 0 / 3**
- median terminal best DU: Arm A **8**, Arm B **8**
- aggregate protected-classical terminal count: Arm A **7**, Arm B **0**
- median minimum terminal ITO: Arm A **6.848039215686274**, Arm B **6.8375**
- preregistered ITO non-inferiority tolerance: Arm A <= Arm B + 0.02 — **PASS**

Every preregistered development check passed:

- classical protection
- deterministic rerun
- DU bridge non-regression
- exact classical budgets
- fresh seed registry exactness
- ITO non-inferiority
- JOINT aggregate advantage
- JOINT success on at least 2/5 seeds
- median best-DU non-regression
- Neural Oracle blocked
- same initial population

## Mechanism result

The multi-hotspot Walsh plateau proposal geometry solved the specific development failure exposed by Phase 1N. On every fresh development seed, Arm A produced at least one terminal candidate that crossed DU and nonlinearity together. Representative JOINT candidates reached:

- DU = 8
- NL = 100
- max |LAT| = 56
- algebraic degree = 7

This is a strong mechanism-level development result under the frozen matched budget. It is not yet confirmatory evidence because the nine reserved confirmation seeds have not been touched.

## Interpretation boundary

This result does **not** establish superiority over the AES S-box. AES remains substantially stronger on the classical reference metrics used here (for example NL 112, DU 4, max correlation 32). This result also does not establish deployment-grade cryptographic security, physical side-channel resistance, or neural co-evolution success. ITO remains a modeled side-channel-related objective and cannot substitute for physical leakage evaluation.

The reserved Phase-1O confirmation seeds remain quarantined:

`2609, 2617, 2621, 2633, 2647, 2657, 2663, 2671, 2683`

They may be used only after a separate confirmation protocol and Gate-1 transition rule are publicly preregistered and committed.