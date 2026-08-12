# AI Intelligence Pipeline

An asynchronous data ingestion and enrichment pipeline for collecting, normalizing, resolving, and validating AI ecosystem intelligence.

## Features

- **Asynchronous Web Ingestion**: Fast concurrency using Python's `asyncio` and `aiohttp`.
- **LEGITIMATE Startup Directory Ingestion**: Ingests 1,100 real AI startups from Y Combinator's company registry.
- **LEGITIMATE AI Product Directory Ingestion**: Ingests 1,100 unique AI tools from the `lakey009/AI-Tools-List` registry, inferring pricing models and canonical startup names.
- **Research Papers Integration**: Retrieves 1,000 papers from ArXiv.
- **GitHub Enrichment**: Correlates research papers to their official repositories and extracts real-time stargazers count.
- **High-Fidelity Signal Ingestion (Jobs & News)**: Collects tech jobs and AI news within the last 24 hours across 5 distinct job boards and 5 distinct news feeds.
- **UTC Date Normalization**: Automatically normalizes all publication dates (including relative times like "3 hours ago") to ISO-8601 UTC format.
- **Multi-Tier LLM Fallback**: Robust fallback chain (Gemini -> Groq -> DeepSeek) falling back gracefully to mock extraction if keys are missing from `.env`.
- **Intelligent Context Chunking**: Splits large documents into 12,000-character segments to prevent HTTP 413 context overflows.
- **Deterministic Entity Resolution**: Standardizes corporate suffixes, casing variations, and alias matches.
- **Structured Schema Validation**: Strictly validates fields against standard records schemas.
- **Automated Export Pipeline**: Flattens and exports all datasets to clean CSV files.

---

## Final Project Dataset Counts

| Data Vertical | Ingestion Source | Output Count (Rows) | CSV File Path |
|---|---|---|---|
| **Startups** | Y Combinator Startup Registry | **1,100** | `data/export_startups.csv` |
| **Products** | AI Tools Database | **1,100** | `data/export_products.csv` |
| **Research Papers** | ArXiv API & GitHub stars | **1,000** | `data/export_research_papers.csv` |
| **Jobs** (<=24h) | Arbeitnow, We Work Remotely, Remotive, Python.org, Jobspresso | **64** | `data/export_jobs.csv` |
| **News** (<=24h) | TechCrunch, MIT Tech Review, VentureBeat, The Decoder, MarkTechPost | **13** | `data/export_news.csv` |
| **Entity Mapping** | Resolved startup name associations | **1,100** | `data/export_entity_mapping_log.csv` |

---

## Technical Documentation & PDF

The detailed design documentation is available in the root directory:
- [architecture.pdf](file:///C:/Users/shrey/OneDrive/Documents/Desktop/AI-Intelligence-Pipeline/architecture.pdf) (exactly 3 pages, generated dynamically)

It covers:
1. Scaling strategies for 500k+ records.
2. Context window (413) and rate-limit (429/403) handling.
3. Freshness tracking and Bloom-filter-based deduplication.
4. Neo4j, pgvector, and PostgreSQL storage integration.

---

## Project Structure

```text
├── src/
│   ├── scrapers/          # Startups, Products, Papers, and GitHub matcher
│   ├── signals/           # Job and News crawlers (last 24 hours)
│   ├── llm/               # Orchestrator, Chunker, and Fallback engine
│   ├── resolver/          # Name standardization and mapping resolver
│   ├── schemas/           # Pydantic schemas and schema validation tests
│   ├── utils/             # Helper scripts (including PDF generation)
│   ├── main.py            # Complete Pipeline Orchestrator (sequential runner)
│   └── export.py          # CSV exporter for data mapping
├── data/                  # JSON files and exported CSVs
├── architecture.pdf       # 3-page Technical Architecture document
├── requirements.txt       # Virtual environment dependencies
└── .gitignore             # Configured to ignore .env and venv
```

---

## Setup & Running the Pipeline

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run the Complete Orchestrated Pipeline
This command executes the full workflow (Startups, Products, Papers, Jobs, News ingestion, Entity Resolution, and CSV exporting):
```powershell
python src/main.py
```

### 3. Run Specific Components Independently
- Startups scraper: `python src/scrapers/startups.py`
- Products scraper: `python src/scrapers/products.py`
- Papers pipeline: `python src/scrapers/papers.py`
- Signals (Jobs & News): `python src/signals/crawler.py`
- Entity resolver: `python src/resolver/apply_resolver.py`
- Exporter: `python src/export.py`
- PDF Re-builder: `python src/utils/generate_pdf.py`
