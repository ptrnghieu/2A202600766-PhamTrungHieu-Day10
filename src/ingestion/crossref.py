from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import requests

from core.config import Settings
from core.utils import compact_join, normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    records: list[PaperRecord] = []

    items = payload.get("message", {}).get("items", [])
    for item in items:
        try:
            doi = item.get("DOI")
            if not doi:
                continue

            title = normalize_whitespace(item.get("title", [""])[0] or "").strip()
            if not title:
                continue

            abstract = normalize_whitespace(item.get("abstract", "") or "").strip()
            if not abstract or len(abstract) < 20:
                continue

            authors_list = []
            for author_data in item.get("author", []):
                given = author_data.get("given", "").strip()
                family = author_data.get("family", "").strip()
                if family:
                    name = f"{given} {family}".strip()
                    if name:
                        authors_list.append(name)

            categories_list = item.get("subject", []) or []
            primary_cat = categories_list[0] if categories_list else "General"

            issued_date = item.get("issued", {})
            date_parts = issued_date.get("date-parts")
            if date_parts and len(date_parts) > 0 and date_parts[0]:
                parts = date_parts[0]
                if len(parts) >= 3:
                    published = f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
                elif len(parts) == 2:
                    published = f"{parts[0]:04d}-{parts[1]:02d}-01"
                else:
                    published = f"{parts[0]:04d}-01-01"
            else:
                published = "2000-01-01"

            updated = published

            abs_url = f"https://doi.org/{doi}"
            pdf_url = ""

            record = PaperRecord(
                paper_id=doi,
                title=title,
                summary=abstract,
                authors=authors_list,
                categories=categories_list,
                primary_category=primary_cat,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment="",
            )
            records.append(record)
        except Exception:
            continue

    return records


def _generate_sample_records(count: int = 24) -> list[PaperRecord]:
    sample_titles = [
        "Large Language Models for Retrieval Augmented Generation",
        "Agentic Retrieval Systems with Neural Networks",
        "Fine-tuning Transformers for Semantic Search",
        "Neural Scaling Laws in Language Models",
        "Reinforcement Learning for Information Retrieval",
        "Knowledge Graphs and Vector Embeddings",
        "Prompt Engineering for LLM-based Systems",
        "Efficient Retrieval with Dense Passage Vectors",
        "Multi-hop Reasoning in Retrieval Augmented Systems",
        "Hybrid Search: Dense and Sparse Retrieval",
        "Evaluating Retrieval Quality in RAG Systems",
        "Domain Adaptation for Specialized Corpora",
        "Context Window Optimization in LLMs",
        "Zero-shot Learning for Cross-domain Retrieval",
        "Memory-efficient Embeddings for Large Collections",
        "Streaming Evaluation of Retrieval Systems",
        "Chain-of-thought Reasoning in Agents",
        "Knowledge Distillation for Efficient Embeddings",
        "Temporal Information in Document Ranking",
        "Multilingual Retrieval Augmented Generation",
        "Robust Retrieval under Noisy Conditions",
        "Interactive Learning for Retrieval Systems",
        "Diversity-aware Ranking in Search",
        "Federated Learning for Privacy-preserving Retrieval",
    ]

    sample_authors = [
        ["Alice Johnson", "Bob Smith"],
        ["Charlie Brown", "Diana Prince", "Eve Wilson"],
        ["Frank Zhang"],
        ["Grace Lee", "Henry Wong"],
        ["Iris Park"],
        ["Jack Turner", "Karen Davis"],
        ["Leo Martin"],
        ["Maya Patel", "Noah Harris"],
        ["Oliver Scott"],
        ["Paula Green"],
    ]

    sample_abstracts = [
        "This paper presents a comprehensive study of retrieval augmented generation systems using large language models. "
        "We evaluate various retrieval strategies and their impact on model performance across multiple benchmarks.",
        "We propose a novel agentic framework for building intelligent retrieval systems. "
        "Our approach demonstrates significant improvements in both accuracy and efficiency compared to baseline methods.",
        "This work explores fine-tuning strategies for transformer models in semantic search applications. "
        "We demonstrate how transfer learning can improve performance with limited labeled data.",
        "We investigate neural scaling laws in language models for retrieval tasks. "
        "Our analysis reveals important insights about model capacity and performance relationships.",
        "This paper introduces a reinforcement learning approach to optimize retrieval systems. "
        "Experimental results show substantial improvements over supervised baselines.",
        "We present methods for integrating knowledge graphs with vector embeddings for enhanced retrieval. "
        "The proposed approach achieves state-of-the-art results on multiple benchmarks.",
        "This work focuses on prompt engineering techniques for improving LLM-based retrieval systems. "
        "We provide practical guidelines for prompt design and optimization.",
        "We propose efficient retrieval methods using dense passage vectors. "
        "Our approach reduces memory requirements while maintaining competitive performance.",
        "This paper addresses multi-hop reasoning in retrieval augmented systems. "
        "We introduce new evaluation metrics and benchmarks for this challenging task.",
        "We explore hybrid search combining dense and sparse retrieval methods. "
        "Experimental results demonstrate the benefits of multi-strategy approaches.",
    ]

    sample_categories = [
        ["Computer Science", "Machine Learning"],
        ["Natural Language Processing", "Information Retrieval"],
        ["Deep Learning", "Neural Networks"],
        ["Text Mining", "Data Science"],
        ["Artificial Intelligence", "Computational Linguistics"],
        ["Information Systems", "Search"],
    ]

    records = []
    for i in range(min(count, len(sample_titles))):
        title = sample_titles[i % len(sample_titles)]
        authors = sample_authors[i % len(sample_authors)]
        summary = sample_abstracts[i % len(sample_abstracts)]
        categories = sample_categories[i % len(sample_categories)]

        published_year = 2024 - (i % 3)
        published_month = 1 + (i % 12)
        published_day = 1 + (i % 28)

        published = f"{published_year:04d}-{published_month:02d}-{published_day:02d}"

        record = PaperRecord(
            paper_id=f"10.xxxx/sample-{i+1:04d}",
            title=title,
            summary=summary,
            authors=authors,
            categories=categories,
            primary_category=categories[0] if categories else "General",
            published=published,
            updated=published,
            abs_url=f"https://doi.org/10.xxxx/sample-{i+1:04d}",
            pdf_url="",
            comment="",
        )
        records.append(record)

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }

    headers = {
        "User-Agent": "DAI2A2026-PhamTrungHieu (ptrnghieu@gmail.com)",
    }

    max_retries = 3
    retry_delays = [1, 2, 4]

    payload = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                payload = response.json()
                break
            elif response.status_code in (429, 503):
                if attempt < max_retries:
                    delay = retry_delays[attempt]
                    time.sleep(delay)
                    continue
                else:
                    if attempt < max_retries:
                        print(f"[WARNING] API returned {response.status_code}, trying fallback...")
                        payload = None
                        break
            else:
                if attempt < max_retries:
                    print(f"[WARNING] API returned {response.status_code}, trying fallback...")
                    payload = None
                    break
        except requests.RequestException as e:
            if attempt < max_retries:
                delay = retry_delays[attempt]
                time.sleep(delay)
                continue
            else:
                print(f"[WARNING] Failed to fetch from CrossRef API: {e}, using fallback...")
                payload = None
                break

    if not payload:
        print("[INFO] Using sample data for testing...")
        records = _generate_sample_records(settings.max_results)
        payload = {
            "message": {
                "items": [
                    {
                        "DOI": r.paper_id,
                        "title": [r.title],
                        "abstract": r.summary,
                        "author": [{"given": name.split()[0], "family": name.split()[-1]} for name in r.authors],
                        "subject": r.categories,
                        "issued": {"date-parts": [[int(r.published.split("-")[0]), int(r.published.split("-")[1]), int(r.published.split("-")[2])]]},
                    }
                    for r in records
                ]
            }
        }
    else:
        records = parse_crossref_payload(payload)

    write_json(settings.paths.raw_api_response, payload)

    write_json(
        settings.paths.raw_records_json,
        [
            {
                "paper_id": r.paper_id,
                "title": r.title,
                "summary": r.summary,
                "authors": r.authors,
                "categories": r.categories,
                "primary_category": r.primary_category,
                "published": r.published,
                "updated": r.updated,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
            }
            for r in records
        ],
    )

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    data = read_json(path)
    records = []
    for item in data:
        record = PaperRecord(
            paper_id=item["paper_id"],
            title=item["title"],
            summary=item["summary"],
            authors=item["authors"],
            categories=item["categories"],
            primary_category=item["primary_category"],
            published=item["published"],
            updated=item["updated"],
            abs_url=item["abs_url"],
            pdf_url=item["pdf_url"],
            comment=item["comment"],
        )
        records.append(record)
    return records
