"""
Data Acquisition Module for NLP Language Trends Analysis.
Queries the arXiv API across four longitudinal epochs (2018-2025) in cs.CL and cs.AI.
Parses, validates, and stores structured metadata and abstracts.
"""

import os
import sys
import time
import json
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

EPOCH_CONFIGS = [
    {
        "epoch": "Epoch 1 (2018-2019)",
        "start_date": "201801010000",
        "end_date": "201912312359",
        "target_count": 500,
        "description": "Pre-Transformer & Early BERT Era"
    },
    {
        "epoch": "Epoch 2 (2020-2021)",
        "start_date": "202001010000",
        "end_date": "202112312359",
        "target_count": 500,
        "description": "Transformer Scaling & Pretraining Era"
    },
    {
        "epoch": "Epoch 3 (2022-2023)",
        "start_date": "202201010000",
        "end_date": "202312312359",
        "target_count": 500,
        "description": "LLM Explosion & Prompting Revolution"
    },
    {
        "epoch": "Epoch 4 (2024-2025)",
        "start_date": "202401010000",
        "end_date": "202512312359",
        "target_count": 500,
        "description": "Agents, Multimodality & Reasoning Era"
    }
]

def fetch_arxiv_batch(search_query: str, start: int = 0, max_results: int = 200, retries: int = 3):
    """Fetches a batch of arXiv records with retry logic and rate-limit compliance."""
    base_url = "https://export.arxiv.org/api/query?"
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "ascending"
    }
    url = base_url + urllib.parse.urlencode(params)
    headers = {"User-Agent": "NLP-Language-Trends-Research/1.0 (academic-corpus; contact: researcher@uni.edu)"}

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read()
                return content
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{retries} failed for query {url[:80]}...: {e}")
            if attempt < retries:
                time.sleep(4 * attempt)
            else:
                logger.error(f"Failed to fetch after {retries} attempts.")
                raise e

def parse_arxiv_xml(xml_content: bytes, epoch_name: str) -> list[dict]:
    """Parses arXiv Atom XML response into clean dictionary records."""
    root = ET.fromstring(xml_content)
    records = []

    for entry in root.findall("atom:entry", ATOM_NS):
        try:
            arxiv_id_elem = entry.find("atom:id", ATOM_NS)
            title_elem = entry.find("atom:title", ATOM_NS)
            summary_elem = entry.find("atom:summary", ATOM_NS)
            published_elem = entry.find("atom:published", ATOM_NS)
            updated_elem = entry.find("atom:updated", ATOM_NS)

            if title_elem is None or summary_elem is None or published_elem is None:
                continue

            raw_id = arxiv_id_elem.text.strip() if arxiv_id_elem is not None else ""
            arxiv_id = raw_id.split("/")[-1]
            title = " ".join(title_elem.text.strip().split())
            abstract = " ".join(summary_elem.text.strip().split())
            published_str = published_elem.text.strip()
            published_dt = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            year = published_dt.year

            # Authors
            authors = []
            for author_elem in entry.findall("atom:author", ATOM_NS):
                name_elem = author_elem.find("atom:name", ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Categories
            categories = []
            primary_cat = ""
            prim_elem = entry.find("arxiv:primary_category", ATOM_NS)
            if prim_elem is not None:
                primary_cat = prim_elem.attrib.get("term", "")

            for cat_elem in entry.findall("atom:category", ATOM_NS):
                term = cat_elem.attrib.get("term", "")
                if term:
                    categories.append(term)

            if not primary_cat and categories:
                primary_cat = categories[0]

            # Filter trivial/empty abstracts
            if len(abstract) < 50:
                continue

            records.append({
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": abstract,
                "published": published_str,
                "year": year,
                "epoch": epoch_name,
                "primary_category": primary_cat,
                "all_categories": ";".join(categories),
                "authors": ";".join(authors[:10]),
                "author_count": len(authors)
            })
        except Exception as err:
            logger.debug(f"Error parsing entry: {err}")
            continue

    return records

def collect_longitudinal_corpus(
    output_raw_json: str = "data/raw/arxiv_nlp_raw.json",
    output_csv: str = "data/processed/arxiv_nlp_corpus.csv",
    force_download: bool = False
) -> pd.DataFrame:
    """Collects arXiv data across the defined epochs or loads existing corpus."""
    if not force_download and os.path.exists(output_csv):
        logger.info(f"Loading cached corpus from {output_csv}...")
        df = pd.read_csv(output_csv)
        logger.info(f"Loaded {len(df)} records across {df['epoch'].nunique()} epochs.")
        return df

    os.makedirs(os.path.dirname(output_raw_json), exist_ok=True)
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    all_records = []
    logger.info("Initiating longitudinal data collection from arXiv API...")

    for config in EPOCH_CONFIGS:
        epoch = config["epoch"]
        target = config["target_count"]
        start_d = config["start_date"]
        end_d = config["end_date"]
        epoch_records = []
        logger.info(f"Fetching {epoch}: target {target} papers between {start_d[:4]} and {end_d[:4]}...")

        # Search cs.CL primarily, plus cs.AI
        query = f"cat:cs.CL AND submittedDate:[{start_d} TO {end_d}]"
        batch_size = 200
        start_idx = 0

        while len(epoch_records) < target:
            to_fetch = min(batch_size, target - len(epoch_records))
            logger.info(f"  Fetching batch at index {start_idx} (target {to_fetch})...")
            try:
                xml_data = fetch_arxiv_batch(query, start=start_idx, max_results=to_fetch)
                batch_records = parse_arxiv_xml(xml_data, epoch)
                if not batch_records:
                    logger.warning(f"  No more records returned for {epoch} at start={start_idx}.")
                    break
                epoch_records.extend(batch_records)
                logger.info(f"  Total collected for {epoch}: {len(epoch_records)}")
                start_idx += len(batch_records)
                time.sleep(3.2)  # Respect arXiv 3-second etiquette
            except Exception as e:
                logger.error(f"  Error fetching batch: {e}")
                break

        all_records.extend(epoch_records)

    # Save raw json
    with open(output_raw_json, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw JSON records ({len(all_records)}) to {output_raw_json}.")

    # Convert to DataFrame, deduplicate, validate
    df = pd.DataFrame(all_records)
    df.drop_duplicates(subset=["arxiv_id"], inplace=True)
    df.drop_duplicates(subset=["title"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info(f"Successfully processed and saved corpus ({len(df)} papers) to {output_csv}.")

    print("\nCorpus Distribution by Epoch:")
    print(df["epoch"].value_counts())
    print("\nCorpus Distribution by Year:")
    print(df["year"].value_counts().sort_index())

    return df

if __name__ == "__main__":
    df = collect_longitudinal_corpus(force_download=True)
    print(f"Data collection complete! Total papers: {len(df)}")
