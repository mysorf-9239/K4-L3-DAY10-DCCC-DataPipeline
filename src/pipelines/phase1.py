from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import load_or_create_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Run the clean baseline pipeline end to end.

    Pseudo-code:
    1. Load settings.
    2. Load hoac fetch raw records.
    3. Clean data.
    4. Save clean CSV/JSON.
    5. Build Chroma index.
    6. Tao hoac load evaluation set.
    7. Evaluate.
    8. Run quality checks va freshness report.
    9. Tao markdown report.
    10. Co the demo agent tren vai sample question.
    """
    settings = load_settings()
    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(settings.paths.raw_records_json)
    clean_df = build_clean_dataframe(records, now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    quality = run_data_quality_checks(clean_df, settings, "baseline")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)
    if not quality["success"]:
        raise RuntimeError("Baseline data failed the quality gate; inspect data/quality/baseline_quality_report.json")

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    test_set = load_or_create_test_set(clean_df, settings.paths.eval_testset, refresh=settings.refresh_test_set)
    if len(test_set) != 10:
        test_set = load_or_create_test_set(clean_df, settings.paths.eval_testset, refresh=True)
    evaluation = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    generate_phase1_report(
        settings.paths.baseline_report,
        {"source": settings.source_api, "raw_records": len(records), "clean_records": len(clean_df)},
        evaluation.summary,
        quality,
        freshness,
    )
    print(f"Baseline complete: {len(clean_df)} clean records")
    print(f"Quality gate: {'PASS' if quality['success'] else 'FAIL'}")
    print(f"Retrieval hit rate: {evaluation.summary['retrieval_hit_rate']:.3f}")
    print(f"Report: {settings.paths.baseline_report}")
