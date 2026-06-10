from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    data = []

    for record in records:
        title = normalize_whitespace(record.title).strip()
        if not title:
            continue

        summary = normalize_whitespace(record.summary).strip()
        if not summary or len(summary) < 50:
            continue

        try:
            published = pd.to_datetime(record.published)
        except Exception:
            published = pd.to_datetime("2000-01-01")

        try:
            updated = pd.to_datetime(record.updated)
        except Exception:
            updated = published

        if published > run_date:
            continue

        age_days = (run_date.date() - published.date()).days

        authors_joined = compact_join(record.authors, ", ")
        categories_joined = compact_join(record.categories, ", ")
        summary_chars = len(summary)
        text_for_embedding = f"{title}\n{summary}\n{authors_joined}".strip()

        data.append(
            {
                "paper_id": record.paper_id,
                "title": title,
                "summary": summary,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "published": published.strftime("%Y-%m-%d"),
                "updated": updated.strftime("%Y-%m-%d"),
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "age_days": age_days,
                "summary_chars": summary_chars,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(data)

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors_joined",
                "categories_joined",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "age_days",
                "summary_chars",
                "text_for_embedding",
            ]
        )
        return df

    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    df = df.sort_values("published", ascending=False).reset_index(drop=True)

    return df
