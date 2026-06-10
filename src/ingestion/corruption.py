from __future__ import annotations

import random
from datetime import timedelta

import pandas as pd

from core.utils import ensure_parent, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    corrupted_df = df.copy()

    log = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "total_rows_input": len(df),
        "corruptions": {
            "dropped_latest_count": 0,
            "blanked_summary_count": 0,
            "noise_injected_count": 0,
            "truncated_titles_count": 0,
            "staled_dates_count": 0,
            "duplicated_rows_count": 0,
        },
        "affected_rows": [],
    }

    drop_fraction = 0.10
    drop_count = max(1, int(len(corrupted_df) * drop_fraction))
    if drop_count > 0:
        corrupted_df = corrupted_df.iloc[drop_count:].copy()
        log["corruptions"]["dropped_latest_count"] = drop_count

    blank_fraction = 0.15
    blank_count = max(0, int(len(corrupted_df) * blank_fraction))
    if blank_count > 0:
        blank_indices = random.sample(range(len(corrupted_df)), blank_count)
        corrupted_df.loc[corrupted_df.index[blank_indices], "summary"] = ""
        log["corruptions"]["blanked_summary_count"] = blank_count

    noise_fraction = 0.20
    noise_count = max(0, int(len(corrupted_df) * noise_fraction))
    if noise_count > 0:
        noise_indices = random.sample(range(len(corrupted_df)), noise_count)
        for idx in noise_indices:
            row_idx = corrupted_df.index[idx]
            current_summary = corrupted_df.loc[row_idx, "summary"]
            noise = "".join(random.choices("!@#$%^&*", k=10))
            corrupted_df.loc[row_idx, "summary"] = f"{current_summary} {noise}"
        log["corruptions"]["noise_injected_count"] = noise_count

    truncate_fraction = 0.10
    truncate_count = max(0, int(len(corrupted_df) * truncate_fraction))
    if truncate_count > 0:
        truncate_indices = random.sample(range(len(corrupted_df)), truncate_count)
        for idx in truncate_indices:
            row_idx = corrupted_df.index[idx]
            current_title = corrupted_df.loc[row_idx, "title"]
            corrupted_df.loc[row_idx, "title"] = current_title[:30]
        log["corruptions"]["truncated_titles_count"] = truncate_count

    stale_fraction = 0.25
    stale_count = max(0, int(len(corrupted_df) * stale_fraction))
    if stale_count > 0:
        stale_indices = random.sample(range(len(corrupted_df)), stale_count)
        for idx in stale_indices:
            row_idx = corrupted_df.index[idx]
            current_published = pd.to_datetime(corrupted_df.loc[row_idx, "published"])
            stale_date = current_published - timedelta(days=365)
            corrupted_df.loc[row_idx, "published"] = stale_date.strftime("%Y-%m-%d")
        log["corruptions"]["staled_dates_count"] = stale_count

    dup_fraction = 0.05
    dup_count = max(0, int(len(df) * dup_fraction))
    if dup_count > 0:
        dup_indices = random.sample(range(len(corrupted_df)), dup_count)
        dup_rows = corrupted_df.iloc[dup_indices].copy()
        corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
        log["corruptions"]["duplicated_rows_count"] = dup_count

    corrupted_df["age_days"] = corrupted_df.apply(
        lambda row: (pd.Timestamp.now(tz="UTC").date() - pd.to_datetime(row["published"]).date()).days,
        axis=1,
    )

    corrupted_df["text_for_embedding"] = corrupted_df.apply(
        lambda row: f"{row['title']}\n{row['summary']}\n{row['authors_joined']}".strip(), axis=1
    )

    log["affected_rows"] = drop_count + blank_count + noise_count + truncate_count + stale_count + dup_count
    log["total_rows_output"] = len(corrupted_df)

    ensure_parent(output_log_path)
    write_json(output_log_path, log)

    return corrupted_df
