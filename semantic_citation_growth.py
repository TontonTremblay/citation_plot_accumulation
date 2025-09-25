#!/usr/bin/env python3
"""semantic_citation_growth.py

Fetch citations for a paper identified by its arXiv ID using the Semantic Scholar
Graph API, export citing-paper metadata to CSV, and plot cumulative citations over
time.

Example
-------
$ python semantic_citation_growth.py 1706.03762 -v

This contacts:
https://api.semanticscholar.org/graph/v1/paper/ARXIV:1706.03762/citations?fields=title,year

No API key is required for up to 100 requests per 5 min.
"""
from __future__ import annotations

import argparse
import csv
import logging
from collections import Counter
from typing import Dict, List, Any, Optional

import matplotlib.pyplot as plt
import pandas as pd
import requests

import warnings
warnings.filterwarnings("ignore", module="matplotlib")

API_BASE = "https://api.semanticscholar.org/graph/v1/paper/"
DEFAULT_FIELDS = "title,year,publicationDate"
LIMIT_PER_PAGE = 1000  # max allowed

logger = logging.getLogger(__name__)


def fetch_citations_arxiv(arxiv_id: str) -> List[Dict[str, Any]]:
    """Return list of citing paper metadata dicts for given arXiv ID."""
    url = f"{API_BASE}ARXIV:{arxiv_id}/citations?fields={DEFAULT_FIELDS}&limit={LIMIT_PER_PAGE}"
    all_data: List[Dict[str, Any]] = []
    while url:
        logger.debug("GET %s", url)
        resp = requests.get(url, timeout=20)
        if resp.status_code != 200:
            raise RuntimeError(f"Semantic Scholar API error {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        items = data.get("data", [])
        for item in items:
            citing = item.get("citingPaper", {})
            all_data.append({
                "title": citing.get("title"),
                "year": citing.get("year"),
                "date": citing.get("publicationDate"),
                "paperId": citing.get("paperId"),
            })
        url = data.get("next")
        logger.debug("Fetched %d citations so far", len(all_data))
    return all_data


def fetch_paper_title(arxiv_id: str) -> Optional[str]:
    url = f"{API_BASE}ARXIV:{arxiv_id}?fields=title"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("title")
    return None


def build_cumulative_series(dates: List[pd.Timestamp], freq: str = "M") -> pd.Series:
    if not dates:
        raise ValueError("No publication dates available")
    s = pd.Series(1, index=pd.to_datetime(dates))
    s = s.resample(freq).sum().cumsum()
    return s


def plot_series(series: pd.Series, title: str, freq_label: str, save_path: str | None = None):
    with plt.xkcd():
        plt.rcParams.update({"font.size": 8})
        fig, ax = plt.subplots(figsize=(8, 5))
        series.plot(marker="o", ax=ax,zorder=10)
        ax.set_ylabel("Cumulative Citations")
        ax.set_xlabel("Date")
        words = title.split()
        title = " ".join(words[:4]) + " …" 
        ax.set_title(f"Cumulative citations over time\n{title}  ({freq_label})")
        fig.subplots_adjust(left=0.15, right=0.95)
        plt.tight_layout()
        if save_path:
            logger.info("Saving plot to %s", save_path)
            fig.savefig(save_path, dpi=150)
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot cumulative citations via Semantic Scholar for an arXiv paper.")
    parser.add_argument("arxiv_id", help="arXiv identifier, e.g. 1706.03762")
    parser.add_argument("--output-file", "-o", default="citations.csv", help="CSV file to write citing-paper metadata")
    parser.add_argument("--plot-file", default=None, help="Filename to save plot (default: <arXivID>_citations.png)")
    parser.add_argument("--freq", choices=["D", "W", "M", "Q", "Y"], default="M", help="Aggregation frequency for cumulative plot (D=day, W=week, M=month [default], Q, Y)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-8s %(message)s",
                        datefmt="%H:%M:%S")

    logger.info("Fetching citations for arXiv:%s", args.arxiv_id)
    title = fetch_paper_title(args.arxiv_id) or f"arXiv:{args.arxiv_id}"
    metadata = fetch_citations_arxiv(args.arxiv_id)
    dates = [pd.to_datetime(d["date"]) for d in metadata if d.get("date")]

    series = build_cumulative_series(dates, freq=args.freq)
    default_plot = f"{args.arxiv_id}_citations.png"
    plot_path = args.plot_file or default_plot
    plot_series(series, title, args.freq, save_path=plot_path)

    logger.info("Writing %d citing papers to %s", len(metadata), args.output_file)
    with open(args.output_file, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=metadata[0].keys())
        writer.writeheader()
        writer.writerows(metadata)


if __name__ == "__main__":
    main()
