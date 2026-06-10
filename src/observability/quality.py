from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import ensure_parent, now_utc, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    null_paper_id_count = df[df["paper_id"].isnull()].shape[0]
    duplicate_paper_ids = len(df) - df["paper_id"].nunique()
    null_title_count = df[df["title"].isnull()].shape[0]
    short_summary_count = df[df["summary"].str.len() < 50].shape[0]
    null_summary_count = df[df["summary"].isnull()].shape[0]

    invalid_dates = 0
    for _, row in df.iterrows():
        try:
            published = pd.to_datetime(row["published"])
            if row["age_days"] > 365 or row["age_days"] < 0:
                invalid_dates += 1
        except Exception:
            invalid_dates += 1

    missing_metadata = df[(df["authors_joined"].isnull()) | (df["categories_joined"].isnull())].shape[0]

    all_checks_passed = (
        null_paper_id_count == 0
        and duplicate_paper_ids == 0
        and null_title_count == 0
        and short_summary_count == 0
        and null_summary_count == 0
    )

    report = {
        "report_name": report_name,
        "run_date": now_utc().isoformat(),
        "row_count": len(df),
        "null_paper_id_count": int(null_paper_id_count),
        "duplicate_paper_ids": int(duplicate_paper_ids),
        "null_title_count": int(null_title_count),
        "short_summary_count": int(short_summary_count),
        "null_summary_count": int(null_summary_count),
        "invalid_dates": int(invalid_dates),
        "missing_metadata": int(missing_metadata),
        "all_checks_passed": bool(all_checks_passed),
    }

    quality_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    ensure_parent(quality_path)
    write_json(quality_path, report)

    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    if df.empty:
        return {
            "latest_published": None,
            "oldest_published": None,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "total_rows": 0,
            "fresh_rows": 0,
            "stale_rows": 0,
            "fresh_percentage": 0.0,
            "is_fresh": False,
        }

    latest_published = df["published"].max()
    oldest_published = df["published"].min()

    fresh_rows = (df["age_days"] <= settings.freshness_threshold_days).sum()
    stale_rows = (df["age_days"] > settings.freshness_threshold_days).sum()
    total_rows = len(df)

    fresh_percentage = (fresh_rows / total_rows * 100) if total_rows > 0 else 0.0
    is_fresh = fresh_percentage >= 70.0

    report = {
        "latest_published": str(latest_published),
        "oldest_published": str(oldest_published),
        "freshness_threshold_days": settings.freshness_threshold_days,
        "total_rows": int(total_rows),
        "fresh_rows": int(fresh_rows),
        "stale_rows": int(stale_rows),
        "fresh_percentage": float(fresh_percentage),
        "is_fresh": bool(is_fresh),
    }

    ensure_parent(report_path)
    write_json(report_path, report)

    return report
