# Corruption Impact Analysis Report

## Metrics Comparison

| Metric | Baseline | Corrupted | Δ | Repaired | Δ |
|--------|----------|-----------|------|----------|------|
| Retrieval Hit Rate | 100.0% | 83.3% | -16.7% | 100.0% | +0.0% |
| Mean Token F1 | 0.921 | 0.775 | -0.146 | 0.921 | +0.000 |
| Judge Accuracy | 100.0% | 83.3% | -16.7% | 100.0% | +0.0% |
| Mean Judge Score | 4.50 | 3.92 | -0.58 | 4.50 | +0.00 |

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

### Corruption Impact

Data corruption reduced retrieval hit rate by 16.7% points (from 100.0% to 83.3%). 
This degradation is correlated with:

- Judge accuracy drop: 16.7% points

- Token F1 decrease: 0.146


### Root Causes

The corruption pipeline applied 6 realistic degradation types:

1. **Dropped latest records** (10%) - Loss of newest content

2. **Blanked summaries** (15%) - Loss of content features

3. **Injected noise** (20%) - Noisy/misleading content

4. **Truncated titles** (10%) - Loss of content context

5. **Stale dates** (25%) - False freshness signals

6. **Duplicate rows** (5%) - Data quality issues


### Recovery Assessment

After repair, hit rate recovered by 16.7% points (from 83.3% to 100.0%). 
✓ **Excellent Recovery:** The repaired dataset matches baseline performance virtually perfectly.

### Key Findings

- **Average Degradation:** 15.6% across all metrics

- **Recovery Rate:** 100.0% of impact reversed

- **Data Rows:** 23 → 24


### Recommendations

1. **Implement Data Quality Monitoring** - Continuous checks to detect corruption early

2. **Version Control for Datasets** - Track data changes over time

3. **Regular Validation** - Test retrieval performance regularly

4. **Source Validation** - Verify data freshness and completeness before indexing

