from __future__ import annotations

from typing import Any
from pathlib import Path

import great_expectations as gx
from great_expectations import expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run the Great Expectations checks and freshness SLA gate.

    Pseudo-code:
    1. Check row count.
    2. Check `paper_id` not null va unique.
    3. Check `title` not null.
    4. Check do dai `summary`.
    5. Check freshness bang `age_days`.
    6. Ghi ket qua vao `data/quality/`.
    """
    context = gx.get_context(mode="ephemeral")
    suffix = "".join(character if character.isalnum() else "_" for character in report_name)
    source = context.data_sources.add_pandas(name=f"papers_source_{suffix}")
    asset = source.add_dataframe_asset(name=f"papers_asset_{suffix}")
    batch_definition = asset.add_batch_definition_whole_dataframe(f"papers_batch_{suffix}")
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30),
    ]
    results = [batch.validate(expectation).to_json_dict() for expectation in expectations]
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    payload = {
        "report_name": report_name,
        "success": all(result["success"] for result in results) and freshness["is_fresh"],
        "expectations_success": all(result["success"] for result in results),
        "freshness_success": freshness["is_fresh"],
        "statistics": {
            "evaluated_expectations": len(results),
            "successful_expectations": sum(bool(result["success"]) for result in results),
            "unsuccessful_expectations": sum(not bool(result["success"]) for result in results),
        },
        "results": results,
        "freshness": freshness,
    }
    report_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"
    write_json(report_path, payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Build and persist a freshness SLA report.

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale.
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    published = pd.to_datetime(df.get("published", pd.Series(dtype="object")), errors="coerce", utc=True)
    age_days = pd.to_numeric(df.get("age_days", pd.Series(dtype="float")), errors="coerce")
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    total_rows = int(len(df))
    stale_ratio = stale_rows / total_rows if total_rows else 1.0
    payload = {
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "latest_published": published.max().date().isoformat() if published.notna().any() else None,
        "oldest_published": published.min().date().isoformat() if published.notna().any() else None,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": stale_ratio,
        "is_fresh": total_rows > 0 and stale_ratio <= 0.25,
    }
    write_json(Path(report_path), payload)
    return payload
