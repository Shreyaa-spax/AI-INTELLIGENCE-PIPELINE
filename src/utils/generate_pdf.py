import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4B5563"))
        
        # Header (on all pages except the cover page if needed, but since it's a short doc, we print on all)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.5)
        self.line(54, 750, 558, 750)
        self.drawString(54, 755, "AI Intelligence Pipeline - Technical Architecture")
        
        # Footer
        self.line(54, 50, 558, 50)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.drawString(54, 38, "FrontierAtlas Data Intelligence Team")
        self.restoreState()

def build_pdf(filename="architecture.pdf"):
    # Target path is the root directory
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles for Sleek Aesthetics
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("AI Intelligence Pipeline", title_style))
    story.append(Paragraph("Technical Architecture & Scale Design Document | FrontierAtlas Team", subtitle_style))
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(Paragraph(
        "This document defines the production architecture for the FrontierAtlas AI Intelligence Pipeline, "
        "designed to collect, normalize, enrich, resolve, and store multi-dimensional intelligence datasets. "
        "The system targets five core verticals: startups, products, research papers, jobs, and news. "
        "Through highly concurrent ingestion, resilient multi-tier LLM fallback, and deterministic entity resolution, "
        "the pipeline converts unstructured web signals into a structured, unified entity graph.",
        body_style
    ))

    # Architecture Overview Table/Flow
    story.append(Paragraph("2. Conceptual Pipeline Workflow", h1_style))
    story.append(Paragraph(
        "The ingest engine operates asynchronously, processing raw inputs through a series of stages:",
        body_style
    ))
    
    workflow_data = [
        ["Stage", "Components", "Primary Technology"],
        ["1. Ingestion", "Async crawlers, API connectors, RSS feed parsers", "Python, asyncio, aiohttp"],
        ["2. Rate Limiting", "Adaptive token buckets, proxy pools, headers matching", "Redis, Backoff + Jitter"],
        ["3. Extraction", "Chunking engine, structured schema validators", "Pydantic, Multi-tier LLM Chain"],
        ["4. Resolution", "Deterministic entity resolver, alias database matcher", "Regex normalizers, corporate parser"],
        ["5. Storage", "Relational database, entity graphs, vector indexes", "PostgreSQL, Neo4j, pgvector"],
        ["6. Delivery", "Automated CSV exports, synced Google Sheets", "Google Sheets API, python-csv"]
    ]
    
    t = Table(workflow_data, colWidths=[1.2*inch, 2.8*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F9FAFB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.HexColor("#F3F4F6")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
        ('TOPPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Page Break for clean section separation
    story.append(PageBreak())

    # Scaling Strategy to 500k
    story.append(Paragraph("3. Horizontal Scale Strategy (500,000+ Records)", h1_style))
    story.append(Paragraph(
        "To scale the pipeline to ingest and process over 500k records without bottlenecks, "
        "the architecture shifts from a single-node sequential script to a distributed event-driven framework:",
        body_style
    ))
    story.append(Paragraph("<b>Distributed Queues:</b> A message broker (e.g., Apache Kafka or RabbitMQ) acts as the ingestion backbone. Tasks are pushed to specific queues (e.g., <i>startup-scrape</i>, <i>paper-enrich</i>) and processed by independent, containerized worker nodes (e.g., Celery or Dramatiq) running in Kubernetes (EKS).", bullet_style))
    story.append(Paragraph("<b>Horizontal Pod Autoscaling:</b> Worker containers scale dynamically based on CPU/memory load and queue backlog depth. This guarantees that during peak periods (e.g., bulk historical crawls), ingestion rates scale without manual server tuning.", bullet_style))
    story.append(Paragraph("<b>Partitioned Processing:</b> Target URLs and API requests are distributed across workers using hash-based partitioning (e.g., partitioning by domain name) to prevent concurrent workers from hammering the same target domain simultaneously.", bullet_style))

    # Handling 413 and 429
    story.append(Paragraph("4. Resiliency & Rate-Limit Strategies (413s & 429s)", h1_style))
    
    story.append(Paragraph("A. Handling 413 Payload Too Large (LLM Context Constraints)", h2_style))
    story.append(Paragraph(
        "Large raw HTML pages, PDF abstracts, or lengthy reports easily trigger 413 HTTP errors or exhaust LLM context windows. "
        "The pipeline resolves this using a <b>Semantic Chunking and Map-Reduce</b> pattern:",
        body_style
    ))
    story.append(Paragraph("<b>Windowed Chunks:</b> The raw text is divided into standard chunks (e.g., max 12,000 characters) preserving sentence and paragraph boundaries.", bullet_style))
    story.append(Paragraph("<b>Map Stage:</b> Each chunk is processed concurrently by the LLM extraction chain to extract entity fields, descriptions, and metadata.", bullet_style))
    story.append(Paragraph("<b>Reduce/Synthesis Stage:</b> The structured outputs are aggregated, resolved, and merged into a single entity record. This dramatically minimizes payload sizes sent to LLM providers.", bullet_style))
    
    story.append(Paragraph("B. Handling 429 Too Many Requests (Adaptive Rate Limiting)", h2_style))
    story.append(Paragraph(
        "Websites and API providers (like ArXiv, GitHub, and LLM endpoints) actively enforce rate limits. "
        "The pipeline employs a multi-tiered rate limiting strategy:",
        body_style
    ))
    story.append(Paragraph("<b>Distributed Token Bucket:</b> Workers use a centralized Redis store to track and acquire rate-limit tokens per domain/provider. This ensures global rate compliance across all distributed nodes.", bullet_style))
    story.append(Paragraph("<b>Adaptive Backoff with Jitter:</b> Requests that fail with 429 or 403 are retried using exponential backoff: <i>t = base^attempt + Jitter</i>, where jitter introduces randomized milliseconds to prevent synchronizing retry waves.", bullet_style))
    story.append(Paragraph("<b>HTTP Header Sniffing:</b> Scrapers inspect `Retry-After` and GitHub's `X-RateLimit-Reset` headers to pause requests dynamically until the exact reset time, preventing token exhaustions.", bullet_style))

    story.append(PageBreak())

    # Freshness Tracking and Deduplication
    story.append(Paragraph("5. Freshness Tracking & Deduplication", h1_style))
    story.append(Paragraph(
        "For jobs and news datasets, the pipeline guarantees absolute freshness (<= 24 hours) and prevents duplicate processing "
        "across worker instances using the following mechanism:",
        body_style
    ))
    story.append(Paragraph("<b>Centralized Idempotency Key:</b> Every crawled item is assigned a unique idempotency key: <i>SHA256(URL + NormalizedTitle)</i>. Before parsing, workers query a global Redis cache; if the key is present, the item is skipped.", bullet_style))
    story.append(Paragraph("<b>Bloom Filters:</b> To scale memory efficiency, Redis Bloom Filters are used to track billions of historically seen URLs with high lookup speed and negligible memory footprints.", bullet_style))
    story.append(Paragraph("<b>UTC Normalization:</b> Raw publication dates (including relative strings like '2 hours ago') are immediately normalized to ISO-8601 UTC format. Records older than 24 hours are discarded during the ingestion phase.", bullet_style))

    # Storage Strategy
    story.append(Paragraph("6. Unified Storage Architecture", h1_style))
    story.append(Paragraph(
        "The production pipeline stores the resolved intelligence in a hybrid storage architecture designed for multi-dimensional querying:",
        body_style
    ))
    
    storage_data = [
        ["Database Type", "Role in Architecture", "Implementation Choice"],
        ["Relational DB", "Stores canonical entity records, jobs, news, and structured metadata. Enables transactional queries and reporting.", "PostgreSQL"],
        ["Graph Database", "Maps relationships between entities. E.g., connecting a Research Paper to its GitHub Repo, and mapping the Startup that owns the Product.", "Neo4j"],
        ["Vector Database", "Stores high-dimensional embeddings of research paper abstracts and product descriptions to enable semantic similarity searches.", "pgvector / Pinecone"]
    ]
    
    st = Table(storage_data, colWidths=[1.5*inch, 3.2*inch, 1.8*inch])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563EB")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 5),
        ('TOPPADDING', (0,0), (-1,0), 5),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F9FAFB")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.HexColor("#F3F4F6")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ('TOPPADDING', (0,1), (-1,-1), 4),
    ]))
    story.append(st)
    story.append(Spacer(1, 15))

    # Build the document using the NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated pdf: {filename}")

if __name__ == "__main__":
    build_pdf("architecture.pdf")
