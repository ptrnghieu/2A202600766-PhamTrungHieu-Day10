from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import ensure_parent, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    if len(df) < 4:
        return []

    sample_size = min(6, len(df))
    sample_indices = [i for i in range(0, len(df), len(df) // sample_size)][:sample_size]
    sample_df = df.iloc[sample_indices].reset_index(drop=True)

    test_items = []
    question_id = 1

    for _, row in sample_df.iterrows():
        paper_id = row["paper_id"]
        title = row["title"]
        summary = row["summary"]
        authors = row["authors_joined"]
        categories = row["categories_joined"]
        published = row["published"]

        first_two_sentences = ". ".join(summary.split(". ")[:2])
        if not first_two_sentences.endswith("."):
            first_two_sentences += "."

        questions = [
            {
                "id": f"q{question_id:03d}",
                "question_type": "summary",
                "question": f"What is the summary of '{title}'?",
                "ground_truth": first_two_sentences,
                "ground_truth_doc_ids": [paper_id],
            },
            {
                "id": f"q{question_id + 1:03d}",
                "question_type": "authors",
                "question": f"Who authored '{title}'?",
                "ground_truth": authors if authors else "Unknown",
                "ground_truth_doc_ids": [paper_id],
            },
            {
                "id": f"q{question_id + 2:03d}",
                "question_type": "date",
                "question": f"When was '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            },
        ]

        if categories:
            questions.append(
                {
                    "id": f"q{question_id + 3:03d}",
                    "question_type": "categories",
                    "question": f"What categories does '{title}' belong to?",
                    "ground_truth": categories,
                    "ground_truth_doc_ids": [paper_id],
                }
            )
            question_id += 4
        else:
            question_id += 3

        test_items.extend(questions)

    ensure_parent(output_path)
    write_json(output_path, test_items)

    return test_items
