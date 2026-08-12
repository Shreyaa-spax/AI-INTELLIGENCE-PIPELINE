# AI Intelligence Pipeline

An asynchronous AI intelligence ingestion pipeline designed for scalable
collection, enrichment, normalization and entity resolution of startups,
products, research papers, jobs and news.

## Architecture

Sources
   ↓
Async Crawlers
   ↓
Raw Data
   ↓
Validation / Normalization
   ↓
GitHub Enrichment
   ↓
LLM Extraction Layer
   ↓
Entity Resolution
   ↓
JSON / CSV Output

## Implemented Components

### Research Papers
- ArXiv ingestion
- Async HTTP requests
- Structured paper extraction
- Author extraction
- Publication date extraction
- GitHub repository matching
- GitHub star extraction

### Signal Ingestion
- News collection
- Job collection
- Source URL tracking
- Timestamp handling

### LLM Orchestration
Implemented multi-provider architecture:

1. Gemini
2. Groq
3. DeepSeek

The system supports provider fallback when one provider fails.

### Entity Resolution

Entity names are normalized against a canonical seed list.

Examples:

Open AI → OpenAI
OpenAI Inc. → OpenAI
HuggingFace → Hugging Face

### Error Handling

The pipeline accounts for:

- HTTP errors
- GitHub API rate limits
- Request failures
- SSL issues
- Missing fields
- LLM provider failures
- Large text chunking

## Scalability

The crawler uses asynchronous operations and can be scaled horizontally
by distributing source workloads across multiple workers.

For production deployment, Redis/Kafka can be used for task queues and
PostgreSQL can be used as the primary persistent database.

A graph database such as Neo4j can store relationships between:

Startup → Product
Startup → Founder
Paper → Author
Paper → Repository
Company → Job

## Data Quality

Every extracted record retains its original source URL.

LLMs are used only for extraction/normalization and not for inventing
source records.

## Running

Create a virtual environment:

python -m venv venv

Activate it:

.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Run the pipeline:

python src/scrapers/papers.py

## Output

Data is stored in the `data/` directory.

Important outputs:

- research_papers.json
- startups.json
- products.json
- jobs.json
- news.json
- entity_mapping_log.json