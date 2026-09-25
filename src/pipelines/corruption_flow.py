from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run corruption, evaluation, idempotent repair, and comparison.

    Pseudo-code:
    1. Load baseline metrics va clean dataset.
    2. Tao corrupted dataframe.
    3. Save corrupted artifacts.
    4. Rebuild index va evaluate.
    5. Run quality checks/freshness tren corrupted data.
    6. Repair lai tu raw records.
    7. Evaluate repaired dataset.
    8. Tao comparison report.
    """
    settings = load_settings()
    required = [settings.paths.clean_json, settings.paths.baseline_metrics, settings.paths.eval_testset]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(f"Run script/run_phase1.py first. Missing artifacts: {', '.join(missing)}")

    clean_df = pd.DataFrame(read_json(settings.paths.clean_json))
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, settings.paths.quality_dir / "corrupted_freshness_report.json"
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_evaluation = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )

    repaired_df = build_clean_dataframe(
        load_raw_records(settings.paths.raw_records_json), now_utc()
    )
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df, settings, settings.paths.quality_dir / "repaired_freshness_report.json"
    )
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    repaired_evaluation = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_evaluation.summary,
        repaired_evaluation.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print("State       Quality   Hit rate   Token F1")
    print(f"Baseline    PASS      {baseline_metrics['retrieval_hit_rate']:.3f}      {baseline_metrics['mean_token_f1']:.3f}")
    print(f"Corrupted   {'PASS' if corrupted_quality['success'] else 'FAIL':<4}      {corrupted_evaluation.summary['retrieval_hit_rate']:.3f}      {corrupted_evaluation.summary['mean_token_f1']:.3f}")
    print(f"Repaired    {'PASS' if repaired_quality['success'] else 'FAIL':<4}      {repaired_evaluation.summary['retrieval_hit_rate']:.3f}      {repaired_evaluation.summary['mean_token_f1']:.3f}")
    print(f"Report: {settings.paths.comparison_report}")
