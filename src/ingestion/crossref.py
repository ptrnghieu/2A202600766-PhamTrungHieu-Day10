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
                    raise RuntimeError(f"API returned {response.status_code} after {max_retries} retries")
            else:
                raise RuntimeError(f"API returned {response.status_code}: {response.text}")
        except requests.RequestException as e:
            if attempt < max_retries:
                delay = retry_delays[attempt]
                time.sleep(delay)
                continue
            else:
                raise RuntimeError(f"Failed to fetch from CrossRef API: {e}")

    if not payload:
        raise RuntimeError("No payload received from CrossRef API")

    write_json(settings.paths.raw_api_response, payload)

    records = parse_crossref_payload(payload)
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
