# Phase 2U — Standard global differential spectrum excludes affine equivalence

**Mathematical property, not a new cryptographic invention.**
Computed independently on 12 selected source S-Boxes (from 19 original
GitHub artifacts), the six historical Phase 2A-T candidates, and the
two previously observed Phase 2T-v1 candidate arrays.

## Definition

For an 8-bit S-Box `S`, define its DDT entries

`D_S(a,b) = |{x in GF(2)^8 : S(x) XOR S(x XOR a) = b}|`,

and define its **global nontrivial differential frequency spectrum** as
the histogram of all `D_S(a,b)` for **255 nonzero values** of `a`
and **all 256 values** of `b`. Every spectrum has exactly
`255*256 = 65,280` entries.

Under an **extended affine (EA) transform**
`T(x) = B(S(A(x) XOR c)) XOR L(x) XOR d`, where `A` and
`B` are invertible GF(2)-linear 8x8 maps and `L` is any
GF(2)-linear map, the rows/columns of the DDT are permuted or shifted
within rows. This **preserves the global histogram of DDT entries**.
Consequently, **different spectra are sufficient to prove that two
S-Boxes are NOT EA-equivalent**. Identical spectra do not imply
equivalence.

## Measured complete spectrum

All verified candidates have DU=8, so the only positive nonzero
DDT entry multiplicities observed are 2, 4, 6 and 8.
The complete histogram also contains the requisite zero entries.

| Research source | S-Box | Count(D=2) | Count(D=4) | Count(D=6) | Count(D=8) |
|---|---|---:|---:|---:|---:|
| historical | 0 | 20150 | 4944 | 762 | 79 |
| historical | 1 | 19875 | 4977 | 821 | 87 |
| historical | 2 | 19933 | 4968 | 805 | 89 |
| historical | 3 | 20134 | 4881 | 796 | 89 |
| historical | 4 | 20159 | 4866 | 799 | 88 |
| historical | 5 | 20248 | 4926 | 728 | 89 |
| blocked v1 | 31019 | 20062 | 4929 | 776 | 98 |
| blocked v1 | 31039 | 20023 | 4959 | 773 | 95 |
| new Phase 2U | 41003 | 20083 | 4908 | 795 | 89 |
| new Phase 2U | 41017 | 20043 | 4974 | 759 | 93 |
| new Phase 2U | 41039 | 20199 | 4815 | 817 | 90 |
| new Phase 2U | 41051 | 20151 | 4902 | 791 | 78 |
| new Phase 2U | 41063 | 20031 | 4995 | 749 | 93 |
| new Phase 2U | 41077 | 19996 | 5019 | 766 | 77 |
| new Phase 2U | 41081 | 20414 | 4851 | 732 | 82 |
| new Phase 2U | 41089 | 19939 | 4977 | 769 | 110 |
| new Phase 2U | 41113 | 20345 | 4878 | 729 | 88 |
| new Phase 2U | 41131 | 20276 | 4932 | 712 | 91 |
| new Phase 2U | 41141 | 20311 | 4848 | 779 | 74 |
| new Phase 2U | 41143 | 19996 | 5010 | 744 | 98 |

**All 20 complete differential frequency spectra are distinct.**
Therefore, none of these twenty S-Boxes belongs to the **same
EA-equivalence class as another**. This is stronger than merely
rejecting S(x XOR a) XOR b clones and verifies candidate diversity
within the selected mathematical equivalence family.

## Research limitations

- These **are not** twenty independent observations of neural
  distinguishing performance. The Phase 2U panel contains **twelve**
  selected candidates; the eight prior S-Boxes are **exclusions only**.
- Distinct spectra do NOT prove source seed stochastic independence,
  cryptographic strength, unknown-key security, equivalence
  outside the EA family, or generalization beyond ToySPN.
- The fact that identical four coarse metrics allow different global
  spectra is consistent with established mathematics and is not an
  original cryptographic primitive or theorem.
- The historical six were computed directly from the original
  `phase2a_candidates.py` source arrays, while the other fourteen
  were computed from the original GitHub ZIP source candidates.
  Independently review the source family to strengthen reproducibility.
- The repository includes a reproducible independent spectrum routine,
  `src/adversarial_sbox/phase2u_affine_invariant.py`,
  and synthetic affine/EA positive and negative control tests in
  `tests/test_phase2u_affine_invariant.py`.
- Exact-head CI success for this new routine must be verified before
  presenting it as GitHub CI validated.

**No new neural model was trained, no predictor ranking was frozen,
and no new security or cryptographic novelty claim follows.**
