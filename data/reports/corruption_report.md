# Corruption, Detection, and Idempotent Repair Report

| State | Quality gate | Freshness | Hit rate | Token F1 | Judge score |
|---|---|---|---:|---:|---:|
| Baseline | PASS | PASS | 1.000 | 0.963 | 4.800 |
| Corrupted | FAIL | FAIL | 0.000 | 0.451 | 2.600 |
| Repaired | PASS | PASS | 1.000 | 0.963 | 4.800 |


## Finding

The controlled corruption suite introduces missing content, noise, truncated titles, stale dates,
duplicate identifiers, and loss of the newest documents. The quality gate detects these defects,
while retrieval and answer metrics quantify the silent failure. Repair rebuilds the dataset from
the immutable raw snapshot, so repeated repair runs produce the same deduplicated result.
