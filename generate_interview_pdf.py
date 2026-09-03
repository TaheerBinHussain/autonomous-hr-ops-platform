"""
Script to generate the Master Interview Preparation Guide PDF for the AI Platform Engineering Project.
Uses ReportLab with custom styles, running footers, tables, and structured sections.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Suppress headers on cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 11 * inch - 36, "AI PLATFORM ENGINEERING & AUTONOMOUS SYSTEMS")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "INTERVIEW MASTER GUIDE")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
            
            # Footer
            self.setFont("Helvetica", 8)
            self.drawString(54, 36, "CONFIDENTIAL — APPLICANT PREPARATION DOCUMENT")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * inch - 54, 36, page_text)
            self.line(54, 46, 8.5 * inch - 54, 46)
            
        self.restoreState()

def build_pdf(filename="AI_Platform_Engineering_Interview_Master_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#0F172A")    # Deep Navy
    SECONDARY = colors.HexColor("#2563EB")  # Electric Blue
    ACCENT = colors.HexColor("#0D9488")     # Teal accent
    TEXT_DARK = colors.HexColor("#1E293B")  # Dark Slate
    BG_LIGHT = colors.HexColor("#F8FAFC")   # Light background
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=PRIMARY,
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=SECONDARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E3A8A"),
        backColor=colors.HexColor("#EFF6FF"),
        borderColor=colors.HexColor("#93C5FD"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=10
    )

    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # COVER PAGE / HEADER BLOCK
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Paragraph("AI Platform Engineering &amp; Autonomous Systems", title_style))
    story.append(Paragraph("Complete Technical Interview Preparation &amp; Architecture Deep-Dive", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=3, color=SECONDARY, spaceBefore=0, spaceAfter=15))

    meta_table_data = [
        [Paragraph("<b>Candidate:</b> Taheer Bin Hussain", body_style), Paragraph("<b>Project:</b> Autonomous HR Ops Platform", body_style)],
        [Paragraph("<b>Role Target:</b> AI Platform / DevOps Engineer", body_style), Paragraph("<b>Repository:</b> github.com/TaheerBinHussain/autonomous-hr-ops-platform", body_style)],
        [Paragraph("<b>Core Stack:</b> FastAPI, n8n, Docker, Mailpit, Qdrant, Postgres", body_style), Paragraph("<b>Status:</b> Production-Grade / Passing CI/CD", body_style)]
    ]
    meta_table = Table(meta_table_data, colWidths=[240, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Executive Overview
    story.append(Paragraph("Executive Overview &amp; Interview Positioning", h1_style))
    story.append(Paragraph(
        "This document provides an exhaustive, end-to-end technical breakdown of the <b>Autonomous HR &amp; Enterprise Operations AI Platform</b>. "
        "Designed to position you at the top 1% of applicants for AI Platform Engineering, DevOps, and Automation Architecture roles, "
        "this guide covers everything from low-level API design to high-level microservice orchestration, database schemas, CI/CD validation, "
        "and anticipated technical interview questions.", body_style
    ))

    # SECTION 1: ELEVATOR PITCH & VALUE PROPOSITION
    story.append(Paragraph("1. The Elevator Pitch &amp; Problem Statement", h1_style))
    
    story.append(Paragraph("1.1 The Business Problem", h2_style))
    story.append(Paragraph(
        "Modern enterprise operations suffer from massive friction in high-volume processes such as talent recruitment, employee onboarding, "
        "and vendor processing. Traditional workflows rely on manual resume review, asynchronous email back-and-forth for interview scheduling, "
        "and delayed IT provisioning (granting GitHub, AWS, and Slack access). This results in high cost-per-hire, candidate drop-off, and operational bottlenecks.", body_style
    ))

    story.append(Paragraph("1.2 The Architectural Solution", h2_style))
    story.append(Paragraph(
        "The project is a fully containerized, microservices-based <b>Autonomous Enterprise Operations Engine</b>. "
        "It combines event-driven orchestration (n8n), an asynchronous Python API microservice (FastAPI), a local test mail server (Mailpit), "
        "and Large Language Model (LLM) reasoning to automate the recruitment lifecycle end-to-end without human intervention.", body_style
    ))

    story.append(Paragraph(
        "<b>Key Technical Pitch (30-Second Interview Response):</b><br/>"
        "<i>'I architected an enterprise AI platform that automates HR recruitment and IT onboarding end-to-end. "
        "Using FastAPI and n8n containerized via Docker Compose, the system ingest candidate resumes, computes dynamic qualification scores (0-100) using LLM reasoning, "
        "autonomously dispatches official offer letters with 3-slot video calendar invites, and triggers automated Day-1 IT access provisioning (GitHub, AWS IAM, Slack) "
        "verified live over a local Mailpit SMTP server.'</i>", callout_style
    ))

    # SECTION 2: SYSTEM ARCHITECTURE & COMPONENT BREAKDOWN
    story.append(Paragraph("2. System Architecture &amp; Component Breakdown", h1_style))
    story.append(Paragraph(
        "The platform comprises 10 decoupled microservices running inside a shared Docker bridge network (<code>automation_net</code>). "
        "Below is the breakdown of each service and its precise role:", body_style
    ))

    services_data = [
        ["Service", "Image / Tech", "Port", "Role & Responsibility in Architecture"],
        ["FastAPI Backend", "Python 3.12-slim", "8000", "Central REST API backend. Serves recruitment routes, AI scoring endpoints, /admin and /apply web portals."],
        ["n8n Engine", "n8nio/n8n:latest", "5678", "Visual workflow orchestrator executing 100 enterprise workflows across 9 business departments."],
        ["Mailpit", "axllent/mailpit", "8025 / 1025", "Local SMTP test server & Web Inbox. Captures sent MIME emails live without external rate limits."],
        ["PostgreSQL", "postgres:16-alpine", "5432", "Relational persistence store for n8n workflow execution history, credential configurations, and application data."],
        ["Redis", "redis:7-alpine", "6379", "In-memory caching layer and task queue management for high-throughput background processing."],
        ["Qdrant", "qdrant/qdrant", "6333", "Vector database storing high-dimensional embeddings for semantic document search and RAG."],
        ["MinIO", "minio/minio", "9000 / 9001", "S3-compatible local object storage handling PDF resume uploads, contract documents, and invoices."],
        ["Prometheus", "prom/prometheus", "9090", "Time-series monitoring server scraping metrics from FastAPI and n8n for system observability."],
        ["Grafana", "grafana/grafana", "3001", "Visualization dashboard providing real-time metrics on workflow runs, memory usage, and API latency."],
        ["Nginx Dashboard", "nginx:alpine", "8085", "Reverse proxy and static asset server displaying the glassmorphism executive dashboard UI."]
    ]

    services_table = Table(services_data, colWidths=[90, 85, 55, 270])
    services_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    story.append(services_table)
    story.append(Spacer(1, 12))

    # SECTION 3: END-TO-END LIFECYCLE WALKTHROUGH
    story.append(Paragraph("3. End-to-End Pipeline Walkthrough (Step-by-Step)", h1_style))
    
    story.append(Paragraph("Step 1: Job Vacancy Creation (HR Admin Portal)", h2_style))
    story.append(Paragraph(
        "HR accesses <code>/admin</code> (served by FastAPI) to publish a new job opening (e.g., <i>Devops Engineer</i>). "
        "The form submits a JSON payload to <code>POST /api/jobs</code> specifying title, offered salary, score threshold (e.g., 75/100), and required skills. "
        "The backend updates the shared in-memory database store <code>JOBS_DB</code>.", body_style
    ))

    story.append(Paragraph("Step 2: Candidate Application (Candidate Portal)", h2_style))
    story.append(Paragraph(
        "Candidates access <code>/apply</code>. On page load, client-side JavaScript calls <code>GET /api/jobs</code> to dynamically populate the job selection dropdown. "
        "Selecting a role auto-fills the matching technical stack and qualification criteria. The candidate inputs their name, email, and resume text.", body_style
    ))

    story.append(Paragraph("Step 3: AI Resume Screening & Evaluation", h2_style))
    story.append(Paragraph(
        "Submitting the application triggers <code>POST /hr/process-candidate-pipeline</code> in FastAPI. "
        "The endpoint passes the candidate's resume and job requirements to <code>ai_service.score_resume()</code>. "
        "The AI analyzes skill overlap, computes a score (0-100), extracts 3 core strengths, and identifies areas for growth. "
        "If <code>score >= threshold</code>, <code>passed</code> is set to <code>True</code>.", body_style
    ))

    story.append(Paragraph("Step 4: AI Technical Interview Scheduling", h2_style))
    story.append(Paragraph(
        "When <code>passed == True</code>, the system automatically generates:<br/>"
        "• An official Offer &amp; Selection Letter.<br/>"
        "• 3 proposed Technical Panel Interview time slots (e.g., <i>Tomorrow at 10:00 AM EST</i>).<br/>"
        "• A custom Jitsi video call meeting URL (e.g., <code>https://meet.jit.si/nexus-interview-sarah-connor</code>).", body_style
    ))

    story.append(Paragraph("Step 5: Day-1 IT Access Provisioning", h2_style))
    story.append(Paragraph(
        "On the HR Admin Panel (<code>/admin</code>), the candidate's record displays an active button: <b>🚀 Trigger Day-1 IT Onboarding</b>. "
        "Clicking this sends a request to <code>POST /api/trigger-onboarding</code>, which provisions GitHub Enterprise access, AWS IAM developer roles, "
        "Slack channel invitations (#welcome, #engineering), and hardware security key dispatches.", body_style
    ))

    story.append(Paragraph("Step 6: Real-Time SMTP Mailpit Dispatch", h2_style))
    story.append(Paragraph(
        "The <code>EmailService</code> uses Python's standard <code>smtplib</code> module to send multipart MIME HTML emails directly to <code>mailpit:1025</code>. "
        "Interviews and IT onboarding packages immediately appear in Mailpit's web inbox (<code>http://localhost:8025</code>) for live verification.", body_style
    ))

    story.append(Spacer(1, 10))

    # SECTION 4: CODE ARCHITECTURE & PATTERNS
    story.append(Paragraph("4. Code Architecture &amp; Key Design Patterns", h1_style))

    story.append(Paragraph("4.1 Asynchronous FastAPI Architecture", h2_style))
    story.append(Paragraph(
        "FastAPI is built on top of <b>Starlette</b> and <b>Pydantic v2</b>, utilizing Python's <code>async/await</code> syntax powered by <code>uvicorn</code> (ASGI server). "
        "This allows non-blocking I/O operations when making external network calls to AI models, database queries, and SMTP dispatchers.", body_style
    ))

    story.append(Paragraph("Sample Code — Asynchronous Candidate Pipeline Endpoint:", h3_style))
    code_snippet = """@router.post("/process-candidate-pipeline", response_model=CandidatePipelineResponse)
async def process_candidate_pipeline(payload: CandidatePipelineRequest) -> CandidatePipelineResponse:
    # 1. AI Resume Scoring
    screen_result = await ai_service.score_resume(payload.resume_text, payload.job_description)
    score = int(screen_result.get("score", 50))
    passed = score >= payload.score_threshold

    # 2. Autonomous Offer & Interview Scheduling
    if passed:
        email_action = "OFFER_LETTER_SENT"
        meet_link = f"https://meet.jit.si/nexus-interview-{payload.candidate_name.lower().replace(' ', '-')}"
        interview_slots = ["Tomorrow at 10:00 AM EST", "Tomorrow at 02:00 PM EST"]

    # 3. SMTP Dispatch to Mailpit
    email_service.send_email(to_email=payload.candidate_email, subject=subject, html_body=html_body)
    return CandidatePipelineResponse(...)"""
    story.append(Paragraph(code_snippet.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Paragraph("4.2 Resilient AI Mock Fallback Architecture", h2_style))
    story.append(Paragraph(
        "To prevent pipeline breakage when third-party LLM APIs (OpenAI/Anthropic) fail, expire, or hit rate limits, "
        "the <code>AIService</code> implements an internal <code>_is_mock()</code> evaluator. "
        "When an API key is missing or detected as a template string (e.g. <code>sk-your-openai-key</code>), the engine automatically executes local keyword-density evaluation algorithms, returning deterministic scoring and realistic structured feedback in &lt;10 milliseconds.", body_style
    ))

    story.append(PageBreak())  # Clean break for Q&A section

    # SECTION 5: ANTICIPATED INTERVIEW QUESTIONS & MODEL ANSWERS
    story.append(Paragraph("5. Hard-Hitting Interview Questions &amp; Model Answers", h1_style))
    story.append(Paragraph("Study these 12 questions carefully. They represent real technical questions asked by Senior Architects and Engineering Managers.", body_style))

    qa_list = [
        (
            "Q1: Walk me through the architecture of your project.",
            "Answer: The platform is a microservices-based architecture containerized with Docker Compose. It features a FastAPI asynchronous backend for REST API endpoints and web portals, n8n for visual workflow automation, PostgreSQL for persistent storage, Redis for queueing/caching, Qdrant for vector embeddings, and Mailpit as a local test SMTP server. Services communicate over an isolated Docker bridge network (automation_net)."
        ),
        (
            "Q2: Why did you choose FastAPI instead of Flask or Django?",
            "Answer: FastAPI was selected because of its native support for Python asynchronous I/O (async/await via ASGI), high performance comparable to Node.js and Go, automatic OpenAPI/Swagger documentation generation, and strict data validation using Pydantic v2."
        ),
        (
            "Q3: What is n8n and why use it alongside FastAPI?",
            "Answer: n8n is an open-source visual workflow automation engine. While FastAPI handles core business APIs and complex LLM scoring, n8n handles visual event orchestration—such as scheduled triggers, webhook listening, and multi-step third-party integrations (Slack, Jira, email digests)—without cluttering backend code."
        ),
        (
            "Q4: Why did you use Mailpit instead of real SMTP like SendGrid or Gmail?",
            "Answer: Mailpit provides an isolated, zero-dependency SMTP trap that runs inside Docker. It allows developers to test and verify MIME HTML email dispatch in real time on port 8025 without exposing production API keys, triggering real-world spam filters, or hitting daily email send quotas during automated CI/CD testing."
        ),
        (
            "Q5: How does your AI service score candidate resumes?",
            "Answer: The AI service receives the job requirements and resume text. In production mode, it sends structured prompts to OpenAI's JSON mode API. In mock/offline mode, it performs keyword overlap analysis against technical terms (Python, Docker, n8n, Kubernetes), computing a percentage score (0-100), extracting strengths, and evaluating against HR's passing threshold."
        ),
        (
            "Q6: How does the HR Admin Panel stay synchronized with the Candidate Portal?",
            "Answer: Both portals interface with stateful FastAPI REST endpoints (/api/jobs and /api/applications). When HR publishes a job on /admin, it updates the backend store. When a candidate opens /apply, client-side JavaScript fetches GET /api/jobs, dynamically updating the job selection dropdown and required skills in real time."
        ),
        (
            "Q7: What happens if an API call to OpenAI fails or times out?",
            "Answer: We implement retry mechanisms using the Tenacity Python library with exponential backoff (retry up to 3 times). If the API fails completely, the service gracefully degrades to local heuristic evaluation, ensuring the user experience never crashes with HTTP 500 errors."
        ),
        (
            "Q8: What vector database did you use and why?",
            "Answer: We integrated Qdrant, an open-source vector database written in Rust. It stores high-dimensional vector embeddings of candidate resumes and internal policy documents, enabling fast cosine similarity searches for Retrieval-Augmented Generation (RAG)."
        ),
        (
            "Q9: How did you set up your CI/CD pipeline?",
            "Answer: We built a GitHub Actions pipeline (.github/workflows/ci.yml). On every git push to main, GitHub Actions runs Python 3.12 dependency installation, linting with Ruff, pytest unit tests, n8n workflow JSON schema validation, and Docker Compose build verification using Docker Compose v2 syntax."
        ),
        (
            "Q10: How do you secure API keys and sensitive environment variables?",
            "Answer: Secrets are managed via a .env file that is explicitly excluded from version control using .gitignore. Environment variables are loaded into FastAPI using pydantic-settings BaseSettings. In production, these secrets would be injected via AWS Secrets Manager or Kubernetes Secrets."
        ),
        (
            "Q11: How would you scale this application to handle 100,000 applicants per day?",
            "Answer: To scale horizontally: 1) Deploy FastAPI backend on Kubernetes (EKS) with Horizontal Pod Autoscaler (HPA) behind an AWS ALB. 2) Offload heavy background tasks (email dispatch, PDF OCR parsing) to Celery workers using Redis/RabbitMQ. 3) Replace SQLite/single-instance Postgres with Amazon Aurora PostgreSQL with read replicas. 4) Use AWS SES or SendGrid for distributed SMTP email delivery."
        ),
        (
            "Q12: How do you ensure data integrity and prevent race conditions?",
            "Answer: In a distributed environment, database transactions would use PostgreSQL row-level locks (SELECT FOR UPDATE) or Redis distributed locks (Redlock) when updating applicant status or decrementing job vacancy quotas."
        )
    ]

    for q, a in qa_list:
        story.append(Paragraph(q, h2_style))
        story.append(Paragraph(a, body_style))
        story.append(Spacer(1, 4))

    # SECTION 6: PRODUCTION SCALING & ROADMAP
    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Production Scaling &amp; Cloud Deployment Plan", h1_style))
    story.append(Paragraph(
        "When an interviewer asks <i>'How would you take this project to production?'</i>, outline this enterprise cloud architecture:", body_style
    ))

    prod_steps = [
        "<b>Cloud Infrastructure:</b> AWS EKS (Elastic Kubernetes Service) for container orchestration across multiple availability zones.",
        "<b>Managed Database:</b> AWS Aurora PostgreSQL Serverless v2 for auto-scaling relational data storage with multi-AZ failover.",
        "<b>Vector Search at Scale:</b> Qdrant Cloud or Managed OpenSearch Cluster for distributed vector search across millions of candidate profiles.",
        "<b>Security &amp; Auth:</b> OAuth2 + JWT authentication for HR users, with RBAC (Role-Based Access Control) and AWS KMS encryption at rest.",
        "<b>Production SMTP:</b> Amazon SES (Simple Email Service) configured with DKIM and SPF records for high email deliverability."
    ]

    for step in prod_steps:
        story.append(Paragraph(f"• {step}", bullet_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=10, spaceAfter=10))
    story.append(Paragraph("<i>End of Guide — Prepared for Technical Interview Success. All Rights Reserved.</i>", ParagraphStyle('FooterNote', parent=body_style, alignment=1, textColor=colors.HexColor("#64748B"))))

    # Build document using custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✅ PDF successfully generated: {os.path.abspath(filename)}")

if __name__ == "__main__":
    build_pdf()
