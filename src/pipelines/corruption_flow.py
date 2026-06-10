from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    run_date = now_utc()

    for path in [
        settings.paths.clean_csv.parent,
        settings.paths.chroma_dir,
        settings.paths.quality_dir,
        settings.paths.comparison_report.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    print("[CorruptionFlow] Loading baseline metrics...")
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    print(f"  Baseline hit rate: {baseline_metrics['retrieval_hit_rate']*100:.1f}%")

    print("[CorruptionFlow] Loading baseline clean dataset...")
    baseline_df = pd.read_csv(settings.paths.clean_csv)
    print(f"  Loaded {len(baseline_df)} records")

    print("[CorruptionFlow] Creating corrupted dataset...")
    corrupted_df = corrupt_clean_dataframe(baseline_df.copy(), settings.paths.corruption_log)
    print(f"  Corrupted to {len(corrupted_df)} records")

    print("[CorruptionFlow] Saving corrupted data...")
    settings.paths.corrupted_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    corrupted_df.to_csv(settings.paths.corrupted_clean_csv, index=False)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    print(f"  Saved to {settings.paths.corrupted_clean_csv}")

    print("[CorruptionFlow] Building corrupted embedding index...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    print(f"  Indexed {len(corrupted_index.documents)} documents")

    print("[CorruptionFlow] Evaluating corrupted dataset...")
    corrupted_eval = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    print(f"  Corrupted hit rate: {corrupted_eval.summary['retrieval_hit_rate']*100:.1f}%")

    print("[CorruptionFlow] Quality checks on corrupted data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    print(f"  Quality: {'✓ PASS' if corrupted_quality['all_checks_passed'] else '✗ FAIL'}")

    print("[CorruptionFlow] Freshness report on corrupted data...")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        settings.paths.quality_dir / "freshness_report_corrupted.json",
    )
    print(f"  Freshness: {corrupted_freshness['fresh_percentage']:.1f}%")

    print("[CorruptionFlow] Repairing data (re-fetching from source)...")
    try:
        records = fetch_source_records(settings)
        print(f"  Fetched {len(records)} records")
    except Exception:
        print("  Failed to fetch from API, using cached raw records")
        records = load_raw_records(settings.paths.raw_records_json)
        print(f"  Loaded {len(records)} cached records")

    repaired_df = build_clean_dataframe(records, run_date)
    print(f"  Repaired to {len(repaired_df)} records")

    print("[CorruptionFlow] Saving repaired data...")
    settings.paths.repaired_clean_csv.parent.mkdir(parents=True, exist_ok=True)
    repaired_df.to_csv(settings.paths.repaired_clean_csv, index=False)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    print(f"  Saved to {settings.paths.repaired_clean_csv}")

    print("[CorruptionFlow] Building repaired embedding index...")
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    print(f"  Indexed {len(repaired_index.documents)} documents")

    print("[CorruptionFlow] Evaluating repaired dataset...")
    repaired_eval = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    print(f"  Repaired hit rate: {repaired_eval.summary['retrieval_hit_rate']*100:.1f}%")

    print("[CorruptionFlow] Quality checks on repaired data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    print(f"  Quality: {'✓ PASS' if repaired_quality['all_checks_passed'] else '✗ FAIL'}")

    print("[CorruptionFlow] Freshness report on repaired data...")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        settings.paths.quality_dir / "freshness_report_repaired.json",
    )
    print(f"  Freshness: {repaired_freshness['fresh_percentage']:.1f}%")

    print("[CorruptionFlow] Generating comparison report...")
    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_eval.summary,
        repaired_eval.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    print(f"  Report saved to {settings.paths.comparison_report}")

    print("\n[CorruptionFlow] ✓ Corruption flow complete!")
    print(f"  Baseline hit rate: {baseline_metrics['retrieval_hit_rate']*100:.1f}%")
    print(f"  Corrupted hit rate: {corrupted_eval.summary['retrieval_hit_rate']*100:.1f}%")
    print(f"  Repaired hit rate: {repaired_eval.summary['retrieval_hit_rate']*100:.1f}%")
    impact = baseline_metrics["retrieval_hit_rate"] - corrupted_eval.summary["retrieval_hit_rate"]
    recovery = repaired_eval.summary["retrieval_hit_rate"] - corrupted_eval.summary["retrieval_hit_rate"]
    print(f"  Impact: -{impact*100:.1f}% | Recovery: +{recovery*100:.1f}%")
