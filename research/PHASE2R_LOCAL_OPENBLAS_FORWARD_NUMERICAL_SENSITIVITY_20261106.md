# Phase 2R — exploratory same-host OpenBLAS kernel numerical sensitivity (2026-11-06)

**Status: independent exploratory *local* probe, NOT an original Phase 2G or prospective Phase 2R science run. No neural training, no optimizer, no gradients, no held-out research data.**

## Original evidence that motivated this probe

[GitHub forward-only run 42129744689](https://github.com/Chatnoir01/ml/actions/runs/42129744689) produced identical stage bytes for seven of seven operations across two different **Haswell** runners. [Separate strict pretraining run 42129744792](https://github.com/Chatnoir01/ml/actions/runs/42129744792) produced matching **16/16** initial weights, data and RNG state hashes, but used **Haswell versus SkylakeX**, making it strictly incomparable as a numerical training control. Six original source ZIP streams were independently verified and packaged (outer SHA-256 `45f59fbcbcf91e69f67ccdf00da47b4b59cb95156d420ac1ae369505cc1c79d8`).

The separately preregistered [within-host GitHub run 42138748840](https://github.com/Chatnoir01/ml/actions/runs/42138748840) executed twice successfully, but both underlying native kernels were **Haswell**. Both correctly declared **`INCONCLUSIVE_NO_DISPATCH_CHANGE`** (7/7 identical within each job); the two original ZIPs + independently recomputed source receipt hashes were preserved as an ephemeral conversation archive `phase2r_20261106_within_host_original_artifacts.zip`, outer SHA-256 **`9c07449790b09a3fcdf173711d6f15b2f7d63fe61113e71bdcd623880886b0ee`**. These runs do NOT test a SkylakeX/Haswell contrast.

## New local exploratory experiment

On the local ChatGPT container (not GitHub's Python 3.12.14 environment), the machine supports AVX-512 and OpenBLAS's `DYNAMIC_ARCH` selection. We ran **three separate Python processes on the same local machine**, each with the same synthetic deterministic float32 inputs and weights but different OpenBLAS kernel selection:

- Python **3.13**, NumPy **2.3.5**, OpenBLAS **0.3.30**, all BLAS numerical thread environment variables = **1**.
- `OPENBLAS_CORETYPE` unset: actual `SkylakeX`.
- `OPENBLAS_CORETYPE=SKYLAKEX`: actual `SkylakeX`, positive same-kernel control.
- `OPENBLAS_CORETYPE=HASWELL`: actual `Haswell`, controlled lower-ISA kernel intervention.
- The data are **NOT Phase 2G historical data or the pinned Phase 2R ToySPN fixture**: these are synthetic random 32-bit values transformed into exactly 256×12 float32 byte features; seed `776003`, chosen to mirror the *registry seed* but without the actual cipher pairing construction.
- Neural shape **12 → 48 → 24 → 1**, with the original Phase 2G seeded initial-normal formula (`786009`), but no training; biases zero, two matrix multiplications, `tanh`, logits, sigmoid. Each stage's C-contiguous little-endian float32 array is hashed with a versioned domain separator.
- Identical source code, data and initialized tensors in all three fresh processes. The true observed OpenBLAS architecture was checked with `threadpoolctl`. No keys or private source data involved.

This is a **demonstration of numerical kernel sensitivity** in a shape-matched proxy, NOT a Phase 2R prospective scientific execution and NOT confirmation of Phase 2G causality.

## Actual numeric observation (SkylakeX vs Haswell on SAME hardware)

| Float32 stage | Different values / total | Max abs difference | Mean abs difference |
|---|---:|---:|---:|
| Synthetic input features | **0 / 3,072** | 0 | 0 |
| First linear GEMM | **1,393 / 12,288** | **3.57627869e-7** | 5.32188219e-9 |
| First tanh | **1,216 / 12,288** | **1.49011612e-7** | 3.71419873e-9 |
| Second linear GEMM | **3,032 / 6,144** | **3.57627869e-7** | 2.71140959e-8 |
| Second tanh | **2,816 / 6,144** | **2.79396772e-7** | 2.13378192e-8 |
| Logits | **192 / 256** | **1.34110451e-7** | 2.94676283e-8 |
| Probabilities | **40 / 256** | **8.94069672e-8** | 8.96397978e-9 |

**Control:** native `SkylakeX` and forced `SKYLAKEX` had **all 7/7 stage SHA-256s identical**.

**Interpretation:** a change in OpenBLAS kernel is sufficient to induce tiny, bit-level floating-point differences in these matched-shape operations under this *local* controlled environment. The first difference occurs at the first GEMM; later float32 stages propagate tiny changes. It is therefore *plausible* that backend variations can explain some model-SHA sensitivity. The effect in an actual trained model remains unknown.

**NOT established:** that the original Phase 2G 64/144 trained SHA discrepancies resulted from CPU/BLAS differences; that any historical runner had the same kernel mismatch; the impact on gradients, Adam steps, optimization trajectory, 2G adaptive-versus-fixed negative verdict or real cipher security. This test does not measure classifier AUC or cryptographic strength.

## Reproducibility and retention

Two standalone exact Python scripts (original hash-only and numeric-array comparison), three per-kernel source JSON receipts, three stage NPZ arrays, independent numeric report and README were packed in a generated *conversation* archive `phase2r_blas_kernel_numeric_difference_evidence_20261106.zip`, **444,722 bytes**, outer SHA-256:

`672dfe3902282d86c345ed9a11a7169832b842bc1a88e894593c99efae8f5001`

**This ZIP has NOT been confirmed in permanent user-owned storage, and must not be represented as an independently hosted, peer-reviewed or indefinitely retrievable scientific dataset.** The full source script is in that archive, rather than in this repository.

Reference on kernel forcing: [OpenBLAS documentation](https://www.openmathlib.org/OpenBLAS/docs/usage/) / [OpenBLAS FAQ](https://github.com/OpenMathLib/OpenBLAS/wiki/Faq), `OPENBLAS_CORETYPE=HASWELL` in a `DYNAMIC_ARCH` build.

## Next evidence gate

A new **separately versioned protocol** would need to rerun the same controlled kernel intervention using the *exact pinned historical Phase 2G numerical software* (Python 3.12.14, NumPy 2.5.3, corresponding OpenBLAS), **the actual pinned 20-S-Box synthetic Phase 2R fixture**, and original byte-exact first-forward data. Only after those results pass could a scientific owner consider separately authorizing an optimizer microstep experiment.

Do not launch full neural training automatically. The old negative verdict `phase2g_adaptive_coevolution_not_supported` remains unchanged. No promotion to main or published security claim is permitted by this exploratory report.
