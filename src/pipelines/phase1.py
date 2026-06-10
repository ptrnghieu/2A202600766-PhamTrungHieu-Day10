from __future__ import annotations

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    settings = load_settings()
    run_date = now_utc()

    for path in [
        settings.paths.raw_api_response.parent,
        settings.paths.clean_csv.parent,
        settings.paths.eval_testset.parent,
        settings.paths.chroma_dir,
        settings.paths.quality_dir,
        settings.paths.gx_dir,
        settings.paths.baseline_report.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)

    if settings.refresh_source or not settings.paths.raw_records_json.exists():
        print("[Phase1] Fetching raw records from CrossRef API...")
        records = fetch_source_records(settings)
        print(f"  Fetched {len(records)} records")
    else:
        print("[Phase1] Loading raw records from cache...")
        records = load_raw_records(settings.paths.raw_records_json)
        print(f"  Loaded {len(records)} records")

    source_summary = {
        "source_api": settings.source_api,
        "query": settings.source_query,
        "filter": settings.source_filter,
        "record_count": len(records),
    }

    print("[Phase1] Cleaning data...")
    df = build_clean_dataframe(records, run_date)
    print(f"  Cleaned to {len(df)} records")
    source_summary["clean_count"] = len(df)

    print("[Phase1] Saving cleaned data...")
    settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.paths.clean_csv, index=False)
    write_json(
        settings.paths.clean_json,
        df.to_dict(orient="records"),
    )
    print(f"  Saved to {settings.paths.clean_csv}")

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        print("[Phase1] Creating evaluation test set...")
        test_set = build_test_set(df, settings.paths.eval_testset)
        print(f"  Created {len(test_set)} test items")
    else:
        print("[Phase1] Loading evaluation test set from cache...")
        test_set = None
        print(f"  Will use existing test set")

    print("[Phase1] Building embedding index...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    print(f"  Indexed {len(index.documents)} documents")

    print("[Phase1] Running evaluation...")
    eval_bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    print(f"  Metrics: {eval_bundle.summary}")

    print("[Phase1] Running data quality checks...")
    quality = run_data_quality_checks(df, settings, "baseline")
    print(f"  Quality: {'✓ PASS' if quality['all_checks_passed'] else '✗ FAIL'}")

    print("[Phase1] Building freshness report...")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f"  Freshness: {freshness['fresh_percentage']:.1f}% fresh")

    print("[Phase1] Generating markdown report...")
    generate_phase1_report(
        settings.paths.baseline_report,
        source_summary,
        eval_bundle.summary,
        quality,
        freshness,
    )
    print(f"  Report saved to {settings.paths.baseline_report}")

    print("[Phase1] Demo agent on sample questions...")
    demo_answers = []
    try:
        require_llm_credentials(settings)
        agent = build_agent(settings, index)
        demo_questions = [
            "What papers discuss reinforcement learning and language models?",
            "Show me papers about agentic systems.",
        ]
        for question in demo_questions:
            try:
                answer = run_agent_question(agent, question)
                demo_answers.append({"question": question, "answer": answer})
                print(f"  Q: {question[:60]}...")
                print(f"  A: {answer[:100] if answer else '(no answer)'}...")
            except Exception as e:
                print(f"  Agent error on question '{question[:40]}...': {e}")
    except Exception as e:
        print(f"  Skipping agent demo: {e}")

    write_json(settings.paths.demo_answers, demo_answers)

    print("\n[Phase1] ✓ Baseline pipeline complete!")
    print(f"  Clean dataset: {len(df)} records")
    print(f"  Test set: {len(test_set) if test_set else '(cached)'} items")
    print(f"  Retrieval hit rate: {eval_bundle.summary['retrieval_hit_rate']*100:.1f}%")
    print(f"  Mean judge score: {eval_bundle.summary['mean_judge_score']:.2f}/5.0")
    print(f"  Data quality: {'✓' if quality['all_checks_passed'] else '✗'}")
    print(f"  Freshness: {'🟢 FRESH' if freshness['is_fresh'] else '🟡 STALE'}")
