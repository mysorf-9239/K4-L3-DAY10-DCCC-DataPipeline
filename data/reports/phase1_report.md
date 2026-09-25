# Phase 1 — Baseline Data Pipeline Report

## Source and lineage

- Source: Crossref REST API
- Raw records: 24
- Clean records: 24

## RAG evaluation

| Metric | Value |
|---|---:|
| Samples | 10 |
| Retrieval hit rate | 1.000 |
| Mean token F1 | 0.963 |
| Judge accuracy | 1.000 |
| Mean judge score | 4.800 |

## Observability

- Quality gate: **PASS**
- Expectations passed: 6/6
- Freshness SLA: **PASS**
- Stale rows: 1/24 (4.2%)
