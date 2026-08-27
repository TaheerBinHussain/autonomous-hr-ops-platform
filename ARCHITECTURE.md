# 🏗 Architecture — AI Automation Platform (Week 5)

## Table of Contents

- [System Overview](#system-overview)
- [Component Descriptions](#component-descriptions)
- [Data Flow Diagrams](#data-flow-diagrams)
- [Workflow Categories & Interactions](#workflow-categories--interactions)
- [Security Considerations](#security-considerations)
- [Scaling Considerations](#scaling-considerations)
- [Monitoring & Observability](#monitoring--observability)
- [Integration Points](#integration-points)

---

## System Overview

The AI Automation Platform is a **microservice-based architecture** composed of 10 containerised services, all orchestrated via Docker Compose. The platform is designed to handle 100 n8n automation workflows spread across 9 business domains, each backed by a shared FastAPI brain, persistent storage layers, and an observable infrastructure.

```
                         ┌──────────────────────────────────┐
                         │         EXTERNAL WORLD           │
                         │   Webhooks / Emails / APIs /     │
                         │   Slack / CRM / ERP / Calendar   │
                         └──────────────┬───────────────────┘
                                        │
                         ┌──────────────▼───────────────────┐
                         │            n8n                   │
                         │   ┌──────────────────────────┐   │
                         │   │  100 Automation Workflows │   │
                         │   │  (Triggers, Logic, HTTP)  │   │
                         │   └──────────┬───────────────┘   │
                         └─────────────┬┘───────────────────┘
                                       │  HTTP / Webhook calls
                         ┌─────────────▼───────────────────┐
                         │         FastAPI Backend          │
                         │  ┌────────┐  ┌───────────────┐  │
                         │  │  AI    │  │   Business    │  │
                         │  │ Layer  │  │    Logic      │  │
                         │  │(OpenAI)│  │  (Routers)    │  │
                         │  └───┬────┘  └───────┬───────┘  │
                         └──────┼───────────────┼──────────┘
                                │               │
               ┌────────────────┼───────────────┼─────────────────┐
               ▼                ▼               ▼                 ▼
       ┌──────────────┐ ┌──────────┐  ┌──────────────┐  ┌──────────────┐
       │  PostgreSQL  │ │  Redis   │  │    Qdrant    │  │    MinIO     │
       │ (Structured  │ │ (Cache / │  │  (Vectors /  │  │  (Files /    │
       │  Relational) │ │  Queue)  │  │     RAG)     │  │  Documents)  │
       └──────────────┘ └──────────┘  └──────────────┘  └──────────────┘

                         ┌───────────────────────────────────┐
                         │         Observability Stack       │
                         │  ┌────────────┐  ┌────────────┐  │
                         │  │ Prometheus │  │  Grafana   │  │
                         │  │ (Metrics)  │  │(Dashboards)│  │
                         │  └────────────┘  └────────────┘  │
                         └───────────────────────────────────┘
```

---

## Component Descriptions

### 1. n8n — Workflow Automation Engine (Port 5678)

**Role:** Visual workflow designer and orchestrator.

n8n is the heart of this platform. It connects external triggers (webhooks, email, schedules, CRM events) to business logic via drag-and-drop workflow nodes. All 100 workflows are stored as JSON and version-controlled in the `workflows/` directory.

**Key responsibilities:**
- Receive incoming webhooks (Slack, email, form submissions)
- Schedule cron-based automations (daily reports, weekly digests)
- Call FastAPI endpoints for AI-powered logic
- Send results to external services (email, Slack, Google Sheets, CRMs)

**Storage:** Workflows and credentials are stored in the shared PostgreSQL instance via `N8N_DB_TYPE=postgresdb`.

---

### 2. FastAPI Backend (Port 8000)

**Role:** AI logic engine and domain API layer.

The backend is a Python 3.12 FastAPI application that exposes ~40 REST endpoints across 9 business domains. It acts as the AI brain — calling OpenAI/Claude, querying Qdrant for semantic search, reading/writing PostgreSQL, caching results in Redis, and storing files in MinIO.

**Router structure:**
```
backend/
├── main.py              # App entry point, middleware, lifespan
├── routers/
│   ├── hr.py            # Resume screening, onboarding, sentiment
│   ├── crm.py           # Lead scoring, churn prediction, follow-ups
│   ├── finance.py       # Invoice extraction, fraud detection
│   ├── support.py       # Ticket classification, response drafting
│   ├── marketing.py     # Campaign generation, SEO, social posts
│   ├── content.py       # Blog posts, email drafts, summaries
│   ├── ops.py           # Incident classification, runbooks
│   ├── supply.py        # Inventory, vendor scoring
│   └── analytics.py     # KPI summaries, trend reports
├── services/
│   ├── ai_service.py    # OpenAI / Claude wrapper
│   ├── rag_service.py   # Qdrant + embeddings
│   ├── storage.py       # MinIO file operations
│   └── cache.py         # Redis caching helpers
├── models/              # Pydantic request/response models
├── tests/               # pytest test suite
└── requirements.txt
```

---

### 3. PostgreSQL 16 (Port 5432)

**Role:** Primary relational database.

Stores all structured, persistent data including:
- n8n workflows, credentials, and execution logs
- Lead/contact records from CRM workflows
- Invoice and expense data
- Support ticket history
- Employee records

Accessed by both FastAPI (via SQLAlchemy/asyncpg) and n8n natively.

---

### 4. Redis 7 (Port 6379)

**Role:** Cache and message queue.

Used for:
- **API response caching** — costly LLM calls cached with TTL
- **Rate-limiting** — prevent runaway API calls to OpenAI
- **Task queuing** — async background tasks (e.g., batch report generation)
- **Session management** — short-lived tokens and session state

---

### 5. Qdrant (Port 6333 / 6334)

**Role:** Vector database for semantic search and RAG.

Every document processed by the platform (resumes, invoices, support tickets, blog posts) is embedded using OpenAI's `text-embedding-3-small` model and stored in Qdrant. This powers:

- **Resume semantic matching** — find top candidates from a vector pool
- **Support ticket deduplication** — detect similar past tickets
- **RAG pipelines** — answer questions against a knowledge base
- **Product recommendation** — match customer queries to products

---

### 6. MinIO (Port 9000 / 9001 UI)

**Role:** S3-compatible object storage.

Stores binary and large-text artifacts:
- Uploaded resumes (PDF, DOCX)
- Invoice images and PDFs
- Generated reports (PDF, XLSX)
- Marketing assets (images, videos)
- Workflow-generated documents

Accessed via the standard boto3/S3 API.

---

### 7. Grafana (Port 3001)

**Role:** Monitoring dashboards.

Pre-configured dashboards show:
- FastAPI request rate, latency, and error rate
- n8n workflow execution counts and failures
- PostgreSQL query performance
- Redis memory usage and hit rate
- Qdrant query latency

---

### 8. Prometheus (Port 9090)

**Role:** Metrics collection.

Scrapes metrics from:
- FastAPI `/metrics` endpoint (via `prometheus-fastapi-instrumentator`)
- PostgreSQL exporter
- Redis exporter
- Node exporter (host metrics)

---

## Data Flow Diagrams

### HR: Resume Screening Flow

```
[Applicant] ──email──► [n8n Email Trigger]
                              │
                    ┌─────────▼──────────┐
                    │  Extract resume    │
                    │  from attachment   │
                    └─────────┬──────────┘
                              │ POST /hr/screen-resume
                    ┌─────────▼──────────┐
                    │  FastAPI Backend   │
                    │  1. Parse text     │
                    │  2. Embed → Qdrant │
                    │  3. GPT-4 score    │
                    │  4. Save → Postgres│
                    └─────────┬──────────┘
                              │ score + analysis
                    ┌─────────▼──────────┐
                    │  n8n: Route result │
                    │  score ≥ 70 → HR   │
                    │  score < 70 → auto │
                    │  rejection email   │
                    └────────────────────┘
```

---

### CRM: Lead Scoring Flow

```
[Web Form / API] ──webhook──► [n8n Webhook Trigger]
                                      │
                            POST /crm/score-lead
                                      │
                         ┌────────────▼───────────┐
                         │    FastAPI Backend      │
                         │  1. Enrich lead data   │
                         │  2. GPT-4 score (0-100)│
                         │  3. Cache in Redis      │
                         │  4. Save to Postgres    │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼───────────┐
                         │  n8n routing logic      │
                         │  score > 80 → Notify   │
                         │  sales rep via Slack    │
                         │  score 50-80 → Nurture  │
                         │  email sequence         │
                         │  score < 50 → Archive   │
                         └─────────────────────────┘
```

---

### Finance: Invoice Processing Flow

```
[Email/Upload] ──► [n8n Trigger]
                        │
              Store PDF → MinIO
                        │
              POST /invoice/extract
                        │
         ┌──────────────▼────────────┐
         │      FastAPI Backend      │
         │  1. OCR / text extract    │
         │  2. GPT-4 structured data │
         │  3. Fraud check           │
         │  4. Save to Postgres      │
         └──────────────┬────────────┘
                        │
         ┌──────────────▼────────────┐
         │  n8n: Approval workflow   │
         │  amount > $10k → manual   │
         │  approval required        │
         │  amount ≤ $10k → auto-    │
         │  approve + notify finance │
         └───────────────────────────┘
```

---

### Support: Ticket Triage Flow

```
[Customer Email / Form] ──► [n8n Trigger]
                                  │
                        POST /support/classify
                                  │
                    ┌─────────────▼──────────────┐
                    │      FastAPI Backend        │
                    │  1. Classify category       │
                    │  2. Detect sentiment        │
                    │  3. Search Qdrant for       │
                    │     similar resolved tix    │
                    │  4. Draft AI response       │
                    │  5. Save ticket to Postgres │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  n8n routing               │
                    │  P1/urgent → Slack alert   │
                    │  Normal → email draft sent │
                    │  Duplicate → link existing │
                    └────────────────────────────┘
```

---

## Workflow Categories & Interactions

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW INTERACTION MAP                         │
│                                                                     │
│  ┌──────────┐    triggers    ┌──────────┐    shares data   ┌─────┐ │
│  │   HR     │◄──────────────►│  Finance │◄────────────────►│Analytics│
│  │ (12 wf)  │                │ (11 wf)  │                  │(10 wf)│ │
│  └──────┬───┘                └──────────┘                  └──┬──┘ │
│         │                                                      │    │
│    new hire                                               aggregates│
│    triggers                                                    │    │
│         │                                                      │    │
│  ┌──────▼───┐    leads       ┌──────────┐    tickets   ┌──────▼──┐ │
│  │  CRM     │◄──────────────►│ Support  │◄────────────►│Marketing│ │
│  │ (14 wf)  │                │ (11 wf)  │              │ (12 wf) │ │
│  └──────────┘                └──────────┘              └─────────┘ │
│                                                                     │
│  ┌──────────┐    alerts      ┌──────────┐    content   ┌─────────┐ │
│  │IT Ops    │◄──────────────►│  Supply  │◄────────────►│Content  │ │
│  │ (10 wf)  │                │ (10 wf)  │              │ (10 wf) │ │
│  └──────────┘                └──────────┘              └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**Cross-domain triggers:**
- HR onboards new employee → CRM creates internal contact → IT creates accounts
- CRM closes deal → Finance creates invoice → Analytics updates revenue KPI
- Support resolves ticket → Marketing gets feedback → Content updates FAQ

---

## Security Considerations

### Authentication & Authorization

| Surface | Mechanism |
|---------|-----------|
| n8n UI | HTTP Basic Auth (`N8N_BASIC_AUTH_USER/PASSWORD`) |
| FastAPI | JWT Bearer tokens + API key middleware |
| PostgreSQL | Username/password, not exposed externally |
| MinIO | Access key / secret key pair |
| Grafana | Username/password auth |

### Network Isolation

All services communicate via Docker's internal `automation-network` bridge network. Only the following ports are exposed to the host:

```
Externally accessible: 3000, 5678, 8000, 9001, 3001, 9090, 6333
Internal only:         5432 (postgres), 6379 (redis), 9000 (minio api)
```

### Secret Management

- All secrets are stored in `.env` (gitignored)
- `.env.example` contains placeholder values only
- Production deployments should use **Docker Secrets** or a **Vault** integration
- OpenAI/Claude keys are never logged or included in responses

### Input Validation

- All FastAPI endpoints use **Pydantic models** for strict input validation
- Text inputs are sanitised before being passed to LLM prompts
- File uploads are scanned for MIME type and size limits enforced

### Rate Limiting

- Redis-backed rate limiting on all AI endpoints (10 req/min per IP default)
- n8n workflow executions tracked and capped to prevent runaway loops

---

## Scaling Considerations

### Horizontal Scaling

| Service | Scale Strategy |
|---------|---------------|
| FastAPI | Multiple replicas behind Nginx/Traefik load balancer |
| n8n | n8n queue mode with multiple worker containers |
| Redis | Redis Cluster or Redis Sentinel for HA |
| PostgreSQL | Read replicas + PgBouncer connection pooling |
| Qdrant | Qdrant distributed cluster mode |
| MinIO | MinIO distributed mode (4+ nodes) |

### Vertical Scaling Recommendations

| Service | Minimum | Recommended (Production) |
|---------|---------|--------------------------|
| FastAPI | 0.5 CPU, 512MB | 2 CPU, 2GB |
| n8n | 0.5 CPU, 512MB | 2 CPU, 4GB |
| PostgreSQL | 1 CPU, 1GB | 4 CPU, 8GB |
| Qdrant | 1 CPU, 2GB | 4 CPU, 16GB |
| Redis | 0.25 CPU, 256MB | 1 CPU, 2GB |

### Caching Strategy

```
Request → Redis Cache Hit? ──Yes──► Return cached response
                │
               No
                │
          FastAPI → OpenAI
                │
          Store in Redis (TTL: 1h for AI responses, 5m for analytics)
                │
          Return response
```

---

## Monitoring & Observability

### Metrics Pipeline

```
FastAPI /metrics ──────────────────────────────────────────►┐
PostgreSQL exporter ────────────────────────────────────────►│ Prometheus
Redis exporter ─────────────────────────────────────────────►│  (scrapes
Node exporter (host) ───────────────────────────────────────►┘  every 15s)
                                                              │
                                                              ▼
                                                           Grafana
                                                        (Dashboards)
                                                              │
                                                    Alert Rules trigger
                                                    Slack / Email alerts
```

### Key Metrics Tracked

| Metric | Alert Threshold |
|--------|----------------|
| FastAPI p99 latency | > 3s |
| Error rate (5xx) | > 1% |
| OpenAI API errors | > 5 in 5m |
| n8n workflow failures | > 3 in 10m |
| PostgreSQL connections | > 80% of max |
| Redis memory | > 75% |
| Disk usage | > 80% |

### Structured Logging

FastAPI uses **structlog** for JSON-formatted logs, making them compatible with:
- **Loki** (Grafana log aggregation)
- **ELK Stack** (Elasticsearch/Logstash/Kibana)
- **CloudWatch** (AWS deployment)

Log format:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",
  "level": "info",
  "service": "fastapi-backend",
  "endpoint": "/hr/screen-resume",
  "duration_ms": 1250,
  "status_code": 200,
  "request_id": "req-abc123"
}
```

---

## Integration Points

### n8n Webhooks

n8n exposes webhook URLs in the format:
```
http://localhost:5678/webhook/{workflow-id}
```

These can be registered as:
- **Slack slash command** endpoints
- **GitHub webhook** receivers
- **CRM event** handlers (HubSpot, Salesforce)
- **Email webhook** targets (SendGrid, Mailgun)

### FastAPI → External Services

```
FastAPI Backend
├── OpenAI API          (GPT-4o, Embeddings)
├── Anthropic API       (Claude 3.5 — fallback)
├── SMTP Server         (Email notifications)
├── Slack Webhook       (Alert delivery)
├── Google APIs         (Calendar, Sheets, Drive)
└── Custom Webhooks     (Any HTTP endpoint)
```

### n8n Built-in Integrations Used

| Category | Integrations |
|----------|-------------|
| Communication | Gmail, Slack, Microsoft Teams, Twilio |
| CRM | HubSpot, Salesforce, Pipedrive |
| Storage | Google Drive, Dropbox, SharePoint |
| Database | PostgreSQL (direct), MySQL, MongoDB |
| Project Mgmt | Jira, Notion, Asana, Linear |
| AI | OpenAI node, Anthropic node |
| Scheduling | Cron, Calendar triggers |

### API Versioning

The FastAPI backend uses URL path versioning:
```
/v1/hr/screen-resume     # Current stable
/v2/hr/screen-resume     # Next version (when introduced)
```

All endpoints currently live under `/v1` (aliased to root for convenience).

---

*Last updated: Week 5 — AI Automation Bootcamp*
