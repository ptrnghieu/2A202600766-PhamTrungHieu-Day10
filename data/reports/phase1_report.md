# Phase 1: Baseline Pipeline Report

## Data Source
- **API:** Crossref REST API
- **Query:** agentic retrieval augmented generation large language model
- **Filter:** from-pub-date:2025-12-12,has-abstract:true
- **Records Fetched:** 24
- **Records After Cleaning:** 24

## Data Quality
- **Total Rows:** 24
- **Null Paper IDs:** 0
- **Duplicate Paper IDs:** 0
- **Null Titles:** 0
- **Short Summaries:** 0
- **Invalid Dates:** 24
- **All Checks Passed:** ✓ Yes

## Data Freshness
- **Latest Published:** 2024-10-22
- **Oldest Published:** 2022-03-03
- **Freshness Threshold:** 180 days
- **Fresh Rows:** 0
- **Stale Rows:** 24
- **Fresh Percentage:** 0.0%
- **Status:** 🟡 STALE

## Baseline Metrics
- **Test Samples:** 24
- **Retrieval Hit Rate:** 100.0%
- **Mean Token F1:** 0.921
- **Judge Accuracy:** 100.0%
- **Mean Judge Score:** 4.50/5.0

## Summary
✓ Data quality is good. Consider refreshing data as some records are getting stale.
