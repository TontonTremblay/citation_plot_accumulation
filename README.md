# Citation Growth Plotter

![Example cumulative citation plot](2411.16537_citation.png)


This repository provides a small utility to visualise how the citation count of a given paper evolves over time, based on data pulled from the open Semantic Scholar Graph API.

## Features

* Retrieves all citing papers for an arXiv-hosted publication via the Semantic Scholar API (no scraping, no captchas).
* Extracts the full publication date of each citation and builds a cumulative counts series at daily / weekly / monthly resolution.
* Produces an xkcd-style cumulative citation curve using `matplotlib`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Scripts

### 1. `semantic_citation_growth.py`  — Semantic Scholar (arXiv-ID)

Fetches citing works for an arXiv paper via the open Semantic Scholar Graph API, writes a CSV, and plots cumulative citations.

```bash
# Monthly (default) aggregation, saves plot as 1706.03762_citations.png
python semantic_citation_growth.py 1706.03762

# Daily aggregation and custom plot file
python semantic_citation_growth.py 1706.03762 --freq D --plot-file figs/attn_daily.png -v
```
