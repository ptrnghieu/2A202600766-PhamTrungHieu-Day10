from __future__ import annotations

from typing import Any

from core.utils import ensure_parent, write_text


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    md = []
    md.append("# Phase 1: Baseline Pipeline Report\n")

    md.append("## Data Source")
    md.append(f"- **API:** {source_summary.get('source_api', 'Unknown')}")
    md.append(f"- **Query:** {source_summary.get('query', 'N/A')}")
    md.append(f"- **Filter:** {source_summary.get('filter', 'N/A')}")
    md.append(f"- **Records Fetched:** {source_summary.get('record_count', 0)}")
    md.append(f"- **Records After Cleaning:** {source_summary.get('clean_count', 0)}")
    md.append("")

    md.append("## Data Quality")
    md.append(f"- **Total Rows:** {quality.get('row_count', 0)}")
    md.append(f"- **Null Paper IDs:** {quality.get('null_paper_id_count', 0)}")
    md.append(f"- **Duplicate Paper IDs:** {quality.get('duplicate_paper_ids', 0)}")
    md.append(f"- **Null Titles:** {quality.get('null_title_count', 0)}")
    md.append(f"- **Short Summaries:** {quality.get('short_summary_count', 0)}")
    md.append(f"- **Invalid Dates:** {quality.get('invalid_dates', 0)}")
    md.append(f"- **All Checks Passed:** {'✓ Yes' if quality.get('all_checks_passed') else '✗ No'}")
    md.append("")

    md.append("## Data Freshness")
    md.append(f"- **Latest Published:** {freshness.get('latest_published', 'N/A')}")
    md.append(f"- **Oldest Published:** {freshness.get('oldest_published', 'N/A')}")
    md.append(f"- **Freshness Threshold:** {freshness.get('freshness_threshold_days', 180)} days")
    md.append(f"- **Fresh Rows:** {freshness.get('fresh_rows', 0)}")
    md.append(f"- **Stale Rows:** {freshness.get('stale_rows', 0)}")
    md.append(f"- **Fresh Percentage:** {freshness.get('fresh_percentage', 0.0):.1f}%")
    md.append(f"- **Status:** {'🟢 FRESH' if freshness.get('is_fresh') else '🟡 STALE'}")
    md.append("")

    md.append("## Baseline Metrics")
    md.append(f"- **Test Samples:** {metrics.get('samples', 0)}")
    md.append(f"- **Retrieval Hit Rate:** {metrics.get('retrieval_hit_rate', 0.0)*100:.1f}%")
    md.append(f"- **Mean Token F1:** {metrics.get('mean_token_f1', 0.0):.3f}")
    md.append(f"- **Judge Accuracy:** {metrics.get('judge_accuracy', 0.0)*100:.1f}%")
    md.append(f"- **Mean Judge Score:** {metrics.get('mean_judge_score', 0.0):.2f}/5.0")
    md.append("")

    md.append("## Summary")
    if quality.get("all_checks_passed") and freshness.get("is_fresh"):
        md.append("✓ Data quality is good and freshness threshold is met. The baseline pipeline is ready for evaluation.")
    elif quality.get("all_checks_passed"):
        md.append("✓ Data quality is good. Consider refreshing data as some records are getting stale.")
    else:
        md.append("⚠ Some data quality issues detected. Review the quality section above.")
    md.append("")

    content = "\n".join(md)
    ensure_parent(report_path)
    write_text(report_path, content)


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
    md = []
    md.append("# Corruption Impact Analysis Report\n")

    def safe_get(d, k, default=0):
        return d.get(k, default) if d else default

    baseline_hit = safe_get(baseline_metrics, "retrieval_hit_rate", 0) * 100
    baseline_f1 = safe_get(baseline_metrics, "mean_token_f1", 0)
    baseline_accuracy = safe_get(baseline_metrics, "judge_accuracy", 0) * 100
    baseline_score = safe_get(baseline_metrics, "mean_judge_score", 0)

    corrupted_hit = safe_get(corrupted_metrics, "retrieval_hit_rate", 0) * 100
    corrupted_f1 = safe_get(corrupted_metrics, "mean_token_f1", 0)
    corrupted_accuracy = safe_get(corrupted_metrics, "judge_accuracy", 0) * 100
    corrupted_score = safe_get(corrupted_metrics, "mean_judge_score", 0)

    repaired_hit = safe_get(repaired_metrics, "retrieval_hit_rate", 0) * 100
    repaired_f1 = safe_get(repaired_metrics, "mean_token_f1", 0)
    repaired_accuracy = safe_get(repaired_metrics, "judge_accuracy", 0) * 100
    repaired_score = safe_get(repaired_metrics, "mean_judge_score", 0)

    md.append("## Metrics Comparison\n")
    md.append("| Metric | Baseline | Corrupted | Δ | Repaired | Δ |")
    md.append("|--------|----------|-----------|------|----------|------|")
    md.append(
        f"| Retrieval Hit Rate | {baseline_hit:.1f}% | {corrupted_hit:.1f}% | {corrupted_hit - baseline_hit:+.1f}% | {repaired_hit:.1f}% | {repaired_hit - baseline_hit:+.1f}% |"
    )
    md.append(
        f"| Mean Token F1 | {baseline_f1:.3f} | {corrupted_f1:.3f} | {corrupted_f1 - baseline_f1:+.3f} | {repaired_f1:.3f} | {repaired_f1 - baseline_f1:+.3f} |"
    )
    md.append(
        f"| Judge Accuracy | {baseline_accuracy:.1f}% | {corrupted_accuracy:.1f}% | {corrupted_accuracy - baseline_accuracy:+.1f}% | {repaired_accuracy:.1f}% | {repaired_accuracy - baseline_accuracy:+.1f}% |"
    )
    md.append(
        f"| Mean Judge Score | {baseline_score:.2f} | {corrupted_score:.2f} | {corrupted_score - baseline_score:+.2f} | {repaired_score:.2f} | {repaired_score - baseline_score:+.2f} |"
    )
    md.append("")

    md.append("## Data Quality Comparison\n")
    md.append("| Metric | Baseline | Corrupted | Repaired |")
    md.append("|--------|----------|-----------|----------|")
    md.append(
        f"| Total Rows | {safe_get(baseline_metrics, 'samples', 0)} | {safe_get(corrupted_quality, 'row_count', 0)} | {safe_get(repaired_quality, 'row_count', 0)} |"
    )
    md.append(
        f"| All Checks Passed | {'✓' if safe_get(corrupted_quality, 'all_checks_passed', False) else '✗'} | {'✓' if safe_get(corrupted_quality, 'all_checks_passed', False) else '✗'} | {'✓' if safe_get(repaired_quality, 'all_checks_passed', False) else '✗'} |"
    )
    md.append("")

    md.append("## Freshness Comparison\n")
    md.append("| Metric | Baseline | Corrupted | Repaired |")
    md.append("|--------|----------|-----------|----------|")
    md.append(
        f"| Fresh Rows | {safe_get(corrupted_freshness, 'fresh_rows', 0)} | {safe_get(corrupted_freshness, 'fresh_rows', 0)} | {safe_get(repaired_freshness, 'fresh_rows', 0)} |"
    )
    md.append(
        f"| Fresh Percentage | - | {safe_get(corrupted_freshness, 'fresh_percentage', 0):.1f}% | {safe_get(repaired_freshness, 'fresh_percentage', 0):.1f}% |"
    )
    md.append(
        f"| Is Fresh | - | {'🟢 Yes' if safe_get(corrupted_freshness, 'is_fresh', False) else '🟡 No'} | {'🟢 Yes' if safe_get(repaired_freshness, 'is_fresh', False) else '🟡 No'} |"
    )
    md.append("")

    md.append("## Analysis\n")
    impact = baseline_hit - corrupted_hit
    recovery = repaired_hit - corrupted_hit

    md.append("### Corruption Impact\n")
    md.append(
        f"Data corruption reduced retrieval hit rate by {impact:.1f}% points "
        f"(from {baseline_hit:.1f}% to {corrupted_hit:.1f}%). "
    )

    judge_impact = baseline_accuracy - corrupted_accuracy
    f1_impact = baseline_f1 - corrupted_f1
    md.append(f"This degradation is correlated with:\n")
    md.append(f"- Judge accuracy drop: {judge_impact:.1f}% points\n")
    md.append(f"- Token F1 decrease: {f1_impact:.3f}\n")
    md.append("")

    md.append("### Root Causes\n")
    md.append("The corruption pipeline applied 6 realistic degradation types:\n")
    md.append("1. **Dropped latest records** (10%) - Loss of newest content\n")
    md.append("2. **Blanked summaries** (15%) - Loss of content features\n")
    md.append("3. **Injected noise** (20%) - Noisy/misleading content\n")
    md.append("4. **Truncated titles** (10%) - Loss of content context\n")
    md.append("5. **Stale dates** (25%) - False freshness signals\n")
    md.append("6. **Duplicate rows** (5%) - Data quality issues\n")
    md.append("")

    md.append("### Recovery Assessment\n")
    md.append(
        f"After repair, hit rate recovered by {recovery:.1f}% points "
        f"(from {corrupted_hit:.1f}% to {repaired_hit:.1f}%). "
    )

    if repaired_hit >= baseline_hit * 0.99:
        md.append("✓ **Excellent Recovery:** The repaired dataset matches baseline performance virtually perfectly.")
    elif repaired_hit >= baseline_hit * 0.95:
        md.append("✓ **Good Recovery:** The repaired dataset closely matches baseline performance.")
    elif repaired_hit >= baseline_hit * 0.85:
        md.append("⚠ **Partial Recovery:** The repaired dataset shows residual degradation, suggesting some data issues persist.")
    else:
        md.append("✗ **Limited Recovery:** The repaired dataset shows significant degradation, indicating repair process issues.")
    md.append("")

    md.append("### Key Findings\n")
    avg_degradation = (judge_impact + (f1_impact * 100)) / 2
    md.append(f"- **Average Degradation:** {abs(avg_degradation):.1f}% across all metrics\n")
    md.append(f"- **Recovery Rate:** {(recovery / impact * 100) if impact > 0 else 100:.1f}% of impact reversed\n")
    md.append(f"- **Data Rows:** {safe_get(corrupted_quality, 'row_count', 0)} → {safe_get(repaired_quality, 'row_count', 0)}\n")
    md.append("")

    md.append("### Recommendations\n")
    if corrupted_quality.get('all_checks_passed') is False:
        md.append("1. **Implement Data Quality Monitoring** - Continuous checks to detect corruption early\n")
    md.append("2. **Version Control for Datasets** - Track data changes over time\n")
    md.append("3. **Regular Validation** - Test retrieval performance regularly\n")
    md.append("4. **Source Validation** - Verify data freshness and completeness before indexing\n")
    md.append("")

    content = "\n".join(md)
    ensure_parent(report_path)
    write_text(report_path, content)
