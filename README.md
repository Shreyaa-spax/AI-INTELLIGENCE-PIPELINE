\# AI Intelligence Pipeline



An asynchronous data ingestion pipeline for collecting and enriching

AI-related startups, products, research papers, jobs and news.



\## Features



\- Asynchronous web crawling using aiohttp

\- ArXiv research paper ingestion

\- GitHub repository matching

\- GitHub star extraction

\- News and job signal collection

\- LLM extraction architecture with provider fallback

\- Intelligent text chunking

\- Deterministic entity resolution

\- JSON and CSV data export



\## Architecture



Sources

→ Async Crawlers

→ Raw Data

→ Validation

→ LLM Extraction

→ GitHub Enrichment

→ Entity Resolution

→ JSON/CSV Output



\## Research Papers



The pipeline collected 1,000 research papers from ArXiv.



GitHub repository matching identified associated repositories where

available.



\## Entity Resolution



The system normalizes company names and maps them to canonical entities.



Examples:



\- Open AI → OpenAI

\- OpenAI Inc. → OpenAI

\- HuggingFace → Hugging Face



\## Error Handling



The system handles:



\- HTTP errors

\- API rate limits

\- request failures

\- missing fields

\- SSL connection issues

\- LLM provider failures

\- large text payloads



\## Scalability



The architecture is designed for horizontal scaling using asynchronous

workers and distributed queues such as Redis or Kafka.



PostgreSQL can be used as the primary database, with object storage for

raw documents and Neo4j for relationship-heavy intelligence queries.



\## Data Quality



Every extracted record retains its source URL.



LLMs are intended for extraction and normalization, not for generating

unsourced records.



\## Current Trial Results



\- Research Papers: 1,000

\- GitHub repositories matched: 154

\- Jobs: 175

\- News: 19

\- Startups: 81



Product extraction requires additional source validation before reaching

the requested 1,000-record target.



\## Project Structure



```text

src/

├── scrapers/

├── signals/

├── llm/

└── resolver/



data/

├── research\_papers.json

├── startups.json

├── jobs.json

├── news.json

└── entity\_mapping\_log.json

