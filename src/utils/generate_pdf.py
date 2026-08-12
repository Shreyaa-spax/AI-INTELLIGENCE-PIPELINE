from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8.5)
        self.setFillColor(colors.HexColor("#4B5563"))
        self.setStrokeColor(colors.HexColor("#D1D5DB"))
        self.line(54, 750, 558, 750)
        self.drawString(54, 758, "AI Intelligence Pipeline | Technical Architecture")
        self.line(54, 48, 558, 48)
        self.drawString(54, 34, "Source-traceable AI ecosystem intelligence")
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf(filename="architecture.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=78,
        bottomMargin=66,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24,
                           leading=28, textColor=colors.HexColor("#1E3A8A"), spaceAfter=6)
    subtitle = ParagraphStyle("Subtitle", parent=styles["BodyText"], fontSize=11, leading=15,
                              textColor=colors.HexColor("#4B5563"), spaceAfter=18)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=14,
                        leading=18, textColor=colors.HexColor("#1E3A8A"), spaceBefore=10, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5,
                        leading=14, textColor=colors.HexColor("#2563EB"), spaceBefore=7, spaceAfter=3)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2,
                          leading=13, textColor=colors.HexColor("#1F2937"), spaceAfter=6)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=14, firstLineIndent=-9, spaceAfter=4)
    small = ParagraphStyle("Small", parent=body, fontSize=8.2, leading=11)

    story = [
        Paragraph("AI Intelligence Pipeline", title),
        Paragraph("Technical Architecture, Reliability & Scale Design", subtitle),
        Paragraph("<b>Purpose.</b> Build a reproducible pipeline that collects AI ecosystem intelligence, validates source data, enriches records, resolves entities, and exports structured datasets.", body),

        Paragraph("1. System Overview", h1),
        Paragraph("The implemented pipeline separates source ingestion from enrichment and export. Network-bound collectors use asynchronous I/O where appropriate; jobs/news are normalized to UTC and filtered to a strict 24-hour freshness window. Every retained signal keeps a source URL so records remain traceable.", body),
    ]

    flow = [
        ["Layer", "Implemented responsibility", "Output"],
        ["Sources", "Startup/product directories, arXiv, GitHub, job feeds, news feeds", "Raw records"],
        ["Ingestion", "asyncio + aiohttp requests, RSS/API parsing, timeouts", "Normalized source items"],
        ["Quality", "Schema validation, UTC date parsing, 24-hour filter, deduplication", "Accepted records"],
        ["Enrichment", "GitHub repository/star matching and LLM extraction/fallback", "Enriched records"],
        ["Resolution", "Canonical names, suffix normalization, aliases", "Entity mappings"],
        ["Delivery", "JSON + CSV export and source coverage report", "Submission datasets"],
    ]
    table = Table(flow, colWidths=[0.9*inch, 3.65*inch, 1.9*inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8.5),
        ("FONTSIZE", (0,1), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.HexColor("#F3F4F6")]),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [table, Spacer(1, 10),
              Paragraph("2. Reliability & Data Quality", h1),
              Paragraph("<b>Freshness:</b> publication timestamps are parsed and normalized to UTC. Jobs and news are retained only when the timestamp is within the preceding 24 hours. Records with unparseable timestamps are rejected rather than assigned a fabricated time.", bullet),
              Paragraph("<b>Deduplication:</b> news uses source URLs as the primary identity; jobs use normalized source URLs and a company/title fallback fingerprint. Duplicate records are removed before export.", bullet),
              Paragraph("<b>Traceability:</b> job and news records retain their source name and URL. The pipeline deliberately does not invent records to satisfy a target count.", bullet),
              Paragraph("<b>Observability:</b> <i>data/signal_source_report.json</i> records per-source fetch status, fresh counts, AI-job counts, unique counts, and duplicate removals.", bullet),
              Paragraph("3. LLM Orchestration", h1),
              Paragraph("The extraction layer uses a multi-tier provider strategy: <b>Gemini → Groq → DeepSeek → Mock fallback</b>. Provider failures can trigger retries with exponential backoff and jitter before the next tier is attempted.", body),
              Paragraph("Large documents are bounded by the chunking layer before LLM submission. The current chunking design uses fixed maximum-size segments so oversized requests do not become a single provider payload. Structured outputs are then validated before downstream resolution/export.", body),
              Paragraph("4. Entity Resolution", h1),
              Paragraph("Entity names are normalized deterministically using casing cleanup, corporate-suffix normalization, aliases, and canonical mappings. This keeps variations such as 'OpenAI', 'Open AI', and 'OpenAI Inc.' closer to one canonical entity without asking the LLM to invent an identity.", body),
              PageBreak(),
              Paragraph("5. Scale Design: 500,000+ Records", h1),
              Paragraph("The current repository is a modular implementation suitable for local execution. At 500k+ records, the same stages can be deployed as horizontally scaled workers without changing the logical data contract:", body),
              Paragraph("<b>Queue-based ingestion:</b> place source tasks on Kafka/RabbitMQ/SQS-style queues and partition work by source/domain.", bullet),
              Paragraph("<b>Worker scaling:</b> run independent crawler, enrichment, and resolution workers; autoscale using queue depth and resource utilization.", bullet),
              Paragraph("<b>Rate control:</b> maintain per-domain/provider concurrency and rate-limit state centrally so multiple workers do not overload one source.", bullet),
              Paragraph("<b>Idempotency:</b> use deterministic URL/content fingerprints so retries and worker restarts do not create duplicate records.", bullet),
              Paragraph("<b>Storage:</b> PostgreSQL for structured records, pgvector for semantic retrieval, and Neo4j when relationship-heavy entity queries justify a graph store.", bullet),
              Paragraph("<b>Observability:</b> collect source latency, error rates, freshness, queue depth, retry counts, and record acceptance/rejection metrics.", bullet),
              Paragraph("6. Failure Handling", h1),
              Paragraph("<b>429 / rate limits:</b> exponential backoff with jitter, respect provider retry/reset hints where available, and fall back to another LLM provider when the failure is provider-specific.", bullet),
              Paragraph("<b>413 / oversized context:</b> chunk source text before LLM submission and process bounded segments rather than sending a complete document in one request.", bullet),
              Paragraph("<b>403 / anti-bot restrictions:</b> treat blocked sources as failed ingestion attempts, record the failure, and do not fabricate replacement records. Production deployments can add browser automation only where permitted by the source's terms.", bullet),
              Paragraph("<b>Partial source failure:</b> one failed source does not terminate the complete pipeline; source-level status is preserved in the coverage report.", bullet),
              Paragraph("7. Storage & Delivery", h1),
    ]

    storage = [
        ["Artifact", "Purpose"],
        ["export_startups.csv", "Startup intelligence"],
        ["export_products.csv", "AI product intelligence"],
        ["export_research_papers.csv", "Research papers + GitHub enrichment"],
        ["export_jobs.csv", "24-hour fresh AI jobs"],
        ["export_news.csv", "24-hour fresh AI news"],
        ["export_entity_mapping_log.csv", "Canonical entity mappings"],
        ["signal_source_report.json", "Live source/freshness/quality diagnostics"],
    ]
    st = Table(storage, colWidths=[2.4*inch, 4.05*inch], repeatRows=1)
    st.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 8.5), ("FONTSIZE", (0,1), (-1,-1), 8.2),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#F9FAFB"), colors.HexColor("#F3F4F6")]),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [st, Spacer(1, 10),
              Paragraph("8. Evaluation & Reproducibility Checklist", h1),
              Paragraph("A clean evaluator run should be able to install requirements, execute the pipeline, inspect the six required CSV datasets, verify source URLs and timestamps, inspect the entity mapping log, and read this document for the 500k+ scaling strategy.", body),
              Paragraph("<b>Current-run note:</b> jobs/news are time-sensitive and their counts change between runs. A source that has no qualifying item inside the 24-hour window is reported as such; the system does not manufacture records to force 5/5 source coverage.", body),
              Paragraph("9. Engineering Principles", h1),
              Paragraph("<b>Traceability over fabricated completeness.</b> Every retained signal should be attributable to a legitimate source.", bullet),
              Paragraph("<b>Validation before export.</b> Freshness, schema, and duplicate checks happen before final CSV generation.", bullet),
              Paragraph("<b>Graceful degradation.</b> Provider/source failures are isolated and observable instead of silently corrupting the dataset.", bullet),
              Paragraph("<b>Scale by infrastructure.</b> The logical stages and record contracts remain stable while workers, queues, and storage scale horizontally.", bullet),
              Spacer(1, 8),
              Paragraph("Generated by src/utils/generate_pdf.py", small)]

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated pdf: {filename}")


if __name__ == "__main__":
    build_pdf("architecture.pdf")
