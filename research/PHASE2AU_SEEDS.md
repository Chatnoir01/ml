# Phase 2A-U frozen seed registry

Public preregistration: #79. Execution lock: #80.

These seeds were fixed before Phase-2A-U implementation/panel reconstruction/neural execution.

## Fresh classical Phase-1O Arm-A source seeds

`(90601, 90617, 90631, 90641, 90647, 90659, 90671, 90677, 90679, 90697, 90703, 90709)`

Each seed must be replayed twice with exactly 340 classical evaluations per replay.

## Fresh neural paired seeds

Dataset seeds:

`(100003, 100019, 100043, 100049, 100057, 100069, 100103, 100109)`

Model seeds:

`(110003, 110017, 110023, 110039, 110051, 110071, 110083, 110107)`

Pairing is positional and fixed.

## Blocked-permutation seeds

- bit-ReLU architecture heterogeneity: `120011`
- byte-tanh architecture heterogeneity: `120017`
- consensus heterogeneity: `120041`

Every blocked test uses exactly 10,000 permutations.

## Frozen split-half indices

- half A: `(0, 1, 2, 3)`
- half B: `(4, 5, 6, 7)`

No seed or split may be replaced/retried/reordered based on scientific results.