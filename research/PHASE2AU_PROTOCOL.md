# Phase 2A-U — 4-round Neural Oracle Qualification Protocol

Public preregistration: issue #82  
Execution lock: issue #83  
Base `main`: `d040f11df1755a06a08fddf92065a29ee31f4d99`

## Purpose

Phase 2A-T replicated a depth-4 peak in S-box-specific separation on fresh seeds. Phase 2A-U asks whether a score restricted to exactly four ToySPN rounds is stable enough across two independent fresh neural replicate blocks to qualify as a reusable candidate-ranking Oracle.

This phase cannot itself authorize or execute GA↔NN feedback.

## Frozen panel

Use exactly `src/adversarial_sbox/phase2a_candidates.py` and panel digest `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`.

All six candidates must revalidate as bijective 8×8 with DU=8, NL=100, max |LAT|=56, algebraic degree=7 and SAC within the existing hard bound.

## Frozen neural regime

- architecture: `byte_tanh_mlp`
- rounds: exactly 4
- differences: `0x00000001`, `0x00000100`
- existing pair generation, split and training procedure unchanged
- no result-driven retries, early stopping or hyperparameter tuning
- no neural evolutionary pressure

## Fresh paired seeds

Block A dataset: `(74003,74017,74027,74047,74059,74071,74093,74101)`  
Block A model: `(84011,84017,84029,84043,84061,84067,84089,84103)`

Block B dataset: `(75011,75017,75029,75041,75061,75083,75109,75121)`  
Block B model: `(85009,85021,85027,85049,85061,85081,85093,85109)`

Blocked permutation seeds: A=`94007`, B=`94009`; exactly 10,000 permutations/block.

A default-branch code search before this protocol commit returned no matches for the new neural seed values. The implementation must additionally enforce exact registry/disjointness checks before execution.

## Exact budget

Each block: 6 candidates × 2 differences × 8 paired replicates = 96 trainings.  
Total: **192 neural trainings exactly**.

## Frozen endpoints

Per block: candidate mean neural advantage over 16 trainings, blocked S-box heterogeneity variance/p-value, candidate score range, mean advantage, existing signal condition, exact candidate rank order.

Across blocks: Spearman correlation of six candidate means, top-2 overlap, per-candidate absolute score difference, mean absolute candidate-score difference (MAD).

## Prerequisites

All required:
1. exact 192 training/provenance count;
2. panel digest and classical revalidation exact;
3. deterministic receipts;
4. signal condition passes in both blocks;
5. neural evolutionary pressure absent;
6. fresh seed registry exact and disjoint from prior frozen neural registries.

Failure of any prerequisite → `phase2au_inconclusive_prerequisites`.

## Qualification criteria

All six required:
1. Block A heterogeneity p < 0.05;
2. Block B heterogeneity p < 0.05;
3. score range >= 0.05 independently in A and B;
4. cross-block Spearman >= 0.80;
5. top-2 overlap >= 1;
6. cross-block MAD <= 0.05.

All pass → `phase2au_oracle_qualified`; otherwise → `phase2au_oracle_not_qualified`.

No criterion may change after scientific execution. Failure is preserved; no in-place retuning.

## Consequence boundary

A PASS only makes a separately preregistered matched-budget Phase 2B eligible. It does not execute co-evolution. Educational/defensive ToySPN only; no deployed-cipher, AES, physical side-channel, production-security or operational key-recovery claim.