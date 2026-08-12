# AI Intelligence Pipeline

> **An asynchronous, source-traceable AI intelligence pipeline for collecting, enriching, resolving, validating, and exporting structured ecosystem data.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Async](https://img.shields.io/badge/Architecture-AsyncIO%20%2B%20aiohttp-informational)](https://docs.python.org/3/library/asyncio.html)
[![Data](https://img.shields.io/badge/Data-CSV%20%2B%20JSON-success)](https://github.com/Shreyaa-spax/AI-INTELLIGENCE-PIPELINE/tree/main/data)

## 1. What this project does

The pipeline ingests AI ecosystem intelligence from public sources and turns it into validated, normalized records. It covers five data areas:

- **Startups** — 1,100 startup records.
- **AI Products** — 1,100 product records.
- **Research Papers** — 1,000 papers, with GitHub repository/star enrichment where available.
- **Jobs** — fresh AI-related jobs discovered inside a strict 24-hour window.
- **News** — fresh AI-related news discovered inside a strict 24-hour window.

The pipeline also performs entity resolution and exports clean CSV datasets plus a source-level validation report.

## 2. Architecture at a glance

```text
                 PUBLIC DATA SOURCES
        ┌──────────┬──────────┬──────────┐
        │ Startups │ Products │ Papers   │
        ├──────────┼──────────┼──────────┤
        │ Jobs     │ News     │ GitHub   │
        └────┬─────┴────┬─────┴────┬─────┘
             │          │          │
             └──────────▼──────────┘
                    ASYNC INGESTION
                  asyncio + aiohttp
                         │
                         ▼
              VALIDATION + NORMALIZATION
              • UTC timestamps
              • schema checks
              • freshness checks
              • duplicate filtering
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       LLM ORCHESTRATOR        ENTITY RESOLUTION
       Gemini → Groq →         canonical names,
       DeepSeek → Mock         aliases, suffixes
             │                       │
             └───────────┬───────────┘
                         ▼
                  STRUCTURED RECORDS
                         │
                  ┌──────┴──────┐
                  ▼             ▼
                JSON           CSV
                  │             │
                  └──────┬──────┘
                         ▼
              SOURCE VALIDATION REPORT
```

See [`architecture.pdf`](./architecture.pdf) for the detailed design, scaling strategy, failure handling, and storage architecture.

## 3. Key engineering features

### Async ingestion
The crawlers use `asyncio` and `aiohttp` to perform network-bound collection without blocking on each request.

### Freshness enforcement
Jobs and news are retained only when their source publication timestamp can be parsed and falls within the **last 24 hours**. Dates are normalized to UTC ISO-8601.

### LLM fallback
The extraction layer follows a multi-tier fallback strategy:

```text
Gemini → Groq → DeepSeek → Mock fallback
```

Transient provider failures are handled with retry/backoff logic rather than immediately abandoning the record.

### Intelligent chunking
Large source documents are split into bounded chunks before LLM processing to reduce context-window failures.

### Entity resolution
Company/startup names are normalized through casing, corporate-suffix cleanup, aliases, and canonical mappings.

### Traceability and no fabricated records
Every collected job/news record retains its source URL. The pipeline does **not** synthesize records to meet a target count. If a source has no qualifying record inside the freshness window, the source report records that outcome.

## 4. Current output snapshot

| Dataset | Current records | Output |
|---|---:|---|
| Startups | 1,100 | `data/export_startups.csv` |
| Products | 1,100 | `data/export_products.csv` |
| Research Papers | 1,000 | `data/export_research_papers.csv` |
| Jobs | 64 in the last verified CSV snapshot | `data/export_jobs.csv` |
| News | 13 in the last verified CSV snapshot | `data/export_news.csv` |
| Entity Mapping | 1,100 | `data/export_entity_mapping_log.csv` |

> **Important:** Jobs/news are time-sensitive. Their counts are expected to change between runs because only qualifying records from the preceding 24 hours are retained. Run the signal crawler to generate the current snapshot.

After running the crawler, inspect `data/signal_source_report.json` for per-source status, freshness counts, AI-job counts, duplicates removed, and sources that produced qualifying records.

## 5. Project structure

```text
AI-INTELLIGENCE-PIPELINE/
├── src/
│   ├── scrapers/
│   │   ├── startups.py
│   │   ├── products.py
│   │   ├── papers.py
│   │   └── github_matcher.py
│   ├── signals/
│   │   └── crawler.py
│   ├── llm/
│   │   ├── orchestrator.py
│   │   └── chunker.py
│   ├── resolver/
│   │   └── entity_resolver.py
│   ├── schemas/
│   ├── utils/
│   ├── main.py
│   └── export.py
├── data/
│   ├── export_startups.csv
│   ├── export_products.csv
│   ├── export_research_papers.csv
│   ├── export_jobs.csv
│   ├── export_news.csv
│   └── export_entity_mapping_log.csv
├── architecture.pdf
├── requirements.txt
├── .env.example
└── README.md
```

## 6. Quick start

### Prerequisites

- Python 3.10+
- Git
- Internet access for source ingestion
- API keys in `.env` for the configured LLM providers when required

### Install

```powershell
python -m pip install -r requirements.txt
copy .env.example .env
```

Add API keys to `.env` as needed. **Never commit `.env`.**

### Run the complete pipeline

```powershell
python src/main.py
```

### Run only jobs/news

```powershell
python src/signals/crawler.py
```

The signal run creates:

```text
 data/jobs.json
 data/news.json
 data/signal_source_report.json
```

### Run individual components

```powershell
python src/scrapers/startups.py
python src/scrapers/products.py
python src/scrapers/papers.py
python src/resolver/apply_resolver.py
python src/export.py
```

## 7. Reproducibility checklist

Before submission, verify:

1. `python src/main.py` completes without an unhandled exception.
2. The three ≥1,000-record datasets contain the expected minimum records.
3. Research-paper GitHub enrichment is present where a repository can be resolved.
4. Jobs/news contain source URLs and timestamps.
5. Jobs/news are filtered to the 24-hour freshness window.
6. `data/signal_source_report.json` records the live source outcomes.
7. `export_entity_mapping_log.csv` is generated.
8. `.env` is not committed to GitHub.
9. `architecture.pdf` is present in the repository root.

## 8. Scaling strategy

The current implementation is designed as a modular ingestion pipeline. For 500k+ records, the same logical stages can be deployed behind a queue with horizontally scaled workers:

```text
Sources → Queue → Async workers → Validation → LLM workers
                                      │
                                      ▼
                             Entity resolution
                                      │
                                      ▼
                         PostgreSQL / pgvector / Neo4j
```

Scaling is achieved by increasing worker capacity, queue partitions, connection pools, rate-limit controls, and storage capacity rather than rewriting the business logic.

## 9. Design principles

- **Source traceability over fabricated completeness.**
- **Freshness is validated, not assumed.**
- **LLM failures degrade gracefully through fallback providers.**
- **Network operations are asynchronous.**
- **Data quality checks happen before export.**
- **The pipeline is modular so individual stages can be tested independently.**

## 10. Submission artifacts

- GitHub repository: `Shreyaa-spax/AI-INTELLIGENCE-PIPELINE`
- `README.md`
- `architecture.pdf`
- `data/export_startups.csv`
- `data/export_products.csv`
- `data/export_research_papers.csv`
- `data/export_jobs.csv`
- `data/export_news.csv`
- `data/export_entity_mapping_log.csv`
- `data/signal_source_report.json`
