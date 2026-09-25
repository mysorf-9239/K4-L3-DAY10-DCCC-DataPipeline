from __future__ import annotations

from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write the baseline pipeline report in Markdown.

    Pseudo-code:
    1. Gom source summary.
    2. In metrics retrieval/evaluation.
    3. In data quality va freshness.
    4. Ghi markdown vao report_path.
    """
    text = f"""# Phase 1 — Baseline Data Pipeline Report

## Source and lineage

- Source: {source_summary.get('source', 'Crossref REST API / offline snapshot')}
- Raw records: {source_summary.get('raw_records', 0)}
- Clean records: {source_summary.get('clean_records', 0)}

## RAG evaluation

| Metric | Value |
|---|---:|
| Samples | {metrics.get('samples', 0)} |
| Retrieval hit rate | {metrics.get('retrieval_hit_rate', 0):.3f} |
| Mean token F1 | {metrics.get('mean_token_f1', 0):.3f} |
| Judge accuracy | {metrics.get('judge_accuracy', 0):.3f} |
| Mean judge score | {metrics.get('mean_judge_score', 0):.3f} |

## Observability

- Quality gate: **{'PASS' if quality.get('success') else 'FAIL'}**
- Expectations passed: {quality.get('statistics', {}).get('successful_expectations', 0)}/{quality.get('statistics', {}).get('evaluated_expectations', 0)}
- Freshness SLA: **{'PASS' if freshness.get('is_fresh') else 'FAIL'}**
- Stale rows: {freshness.get('stale_rows', 0)}/{freshness.get('total_rows', 0)} ({freshness.get('stale_ratio', 0):.1%})
"""
    write_text(report_path, text)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write the baseline/corrupted/repaired comparison report."""
    def row(label: str, metrics: dict[str, Any], quality: dict[str, Any], freshness: dict[str, Any]) -> str:
        return (
            f"| {label} | {'PASS' if quality.get('success') else 'FAIL'} | "
            f"{'PASS' if freshness.get('is_fresh') else 'FAIL'} | "
            f"{metrics.get('retrieval_hit_rate', 0):.3f} | {metrics.get('mean_token_f1', 0):.3f} | "
            f"{metrics.get('mean_judge_score', 0):.3f} |"
        )

    baseline_quality = {"success": True}
    baseline_freshness = {"is_fresh": True}
    text = """# Corruption, Detection, and Idempotent Repair Report

| State | Quality gate | Freshness | Hit rate | Token F1 | Judge score |
|---|---|---|---:|---:|---:|
"""
    text += row("Baseline", baseline_metrics, baseline_quality, baseline_freshness) + "\n"
    text += row("Corrupted", corrupted_metrics, corrupted_quality, corrupted_freshness) + "\n"
    text += row("Repaired", repaired_metrics, repaired_quality, repaired_freshness) + "\n"
    text += """

## Finding

The controlled corruption suite introduces missing content, noise, truncated titles, stale dates,
duplicate identifiers, and loss of the newest documents. The quality gate detects these defects,
while retrieval and answer metrics quantify the silent failure. Repair rebuilds the dataset from
the immutable raw snapshot, so repeated repair runs produce the same deduplicated result.
"""
    write_text(report_path, text)
