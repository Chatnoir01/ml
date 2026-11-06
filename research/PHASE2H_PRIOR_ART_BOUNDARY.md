# Phase 2H — Prior-art boundary

This note freezes the novelty boundary used while interpreting Phase 2H. It does
not change any experimental criterion.

## What prior work already establishes

The general ideas below are not claimed as novel:

1. Surrogate/model-management strategy can materially change evolutionary search
   behaviour even when the learned model itself is useful.
2. Online surrogate-assisted evolutionary algorithms update learned models from
   newly evaluated candidates.
3. Coevolution can exhibit drift/cycling and loss of historical progress.
4. Historical archives / Hall-of-Fame mechanisms are established techniques for
   testing or mitigating such failures.

Representative prior work includes Rosin & Belew (1997), later reviews of
surrogate-assisted evolutionary computation/model management, and recent
controlled work on the interaction between surrogate accuracy and model
management strategy.

## What Phase 2G/2H may contribute if the evidence supports it

The project must not claim invention of GA↔NN feedback, adaptive model
management, curriculum adaptation, cycling, or archives.

The narrower candidate contribution is the controlled empirical pattern in this
specific protocol:

- a genuinely active bidirectional adaptive arm;
- explicit C/F/A/S controls;
- adaptation and cross-key mechanism activity demonstrated;
- adaptive A better than C and S under the frozen criteria;
- fixed-retraining F better than A on all nine frozen seeds;
- a frozen-artifact mechanistic diagnosis of why the extra coadaptation failed.

A stronger contribution requires Phase 2H to identify a preregistered mechanism,
Phase 2I to intervene specifically on that mechanism using fresh validation
seeds/holdout, and Phase 2J to replicate independently.

## Claim discipline

Allowed now:
"Phase 2G produced a controlled negative result and Phase 2H is diagnosing the
mechanism from frozen artifacts."

Not allowed now:
"we discovered a new universal law", "we invented bidirectional GA↔NN
coevolution", or "curriculum replacement caused the failure".

Any causal statement must wait for a targeted intervention and independent
replication.
