# Corruption Impact Analysis Report

## Metrics Comparison

| Metric | Baseline | Corrupted | Δ | Repaired | Δ |
|--------|----------|-----------|------|----------|------|
| Retrieval Hit Rate | 100.0% | 66.7% | -33.3% | 100.0% | +0.0% |
| Mean Token F1 | 0.921 | 0.581 | -0.340 | 0.921 | +0.000 |
| Judge Accuracy | 100.0% | 62.5% | -37.5% | 100.0% | +0.0% |
| Mean Judge Score | 4.50 | 3.17 | -1.33 | 4.50 | +0.00 |

## Data Quality Comparison

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Total Rows | 24 | 23 | 24 |
| All Checks Passed | ✗ | ✗ | ✓ |

## Freshness Comparison

| Metric | Baseline | Corrupted | Repaired |
|--------|----------|-----------|----------|
| Fresh Rows | 0 | 0 | 0 |
| Fresh Percentage | - | 0.0% | 0.0% |
| Is Fresh | - | 🟡 No | 🟡 No |

## Analysis

**Corruption Impact:** Data corruption reduced retrieval hit rate by 33.3% points (from 100.0% to 66.7%). 
**Recovery Success:** After repair, hit rate recovered by 33.3% points (from 66.7% to 100.0%), demonstrating the effectiveness of the repair process. 
Overall, the repaired dataset closely matches baseline performance.
