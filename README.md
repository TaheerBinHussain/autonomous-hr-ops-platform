# 🤖 AI Automation Platform — Week 5

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)](https://n8n.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> **Production-grade company automation suite powered by 100 AI workflows.**  
> Built with FastAPI, n8n, OpenAI, LangChain, PostgreSQL, Redis, MinIO, Qdrant, Grafana, and more — all orchestrated via Docker Compose.

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [What's Included](#-whats-included)
- [Quick Start](#-quick-start)
- [Services](#-services)
- [API Endpoints](#-api-endpoints)
- [Workflow Importing](#-workflow-importing)
- [Environment Variables](#-environment-variables)
- [Development](#-development)
- [Tech Stack](#-tech-stack)
- [Week 5 Bootcamp Context](#-week-5-bootcamp-context)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI AUTOMATION PLATFORM                           │
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │   Dashboard  │    │     n8n      │    │       FastAPI Backend     │  │
│  │  (React/Vite)│    │  Workflow    │    │  /hr  /crm  /finance      │  │
│  │ :3000        │◄──►│  Engine      │◄──►│  /support /content /ops   │  │
│  └──────────────┘    │ :5678        │    │  :8000                   │  │
│                      └──────┬───────┘    └────────────┬─────────────┘  │
│                             │                         │                 │
│          ┌──────────────────┼─────────────────────────┤                 │
│          ▼                  ▼                         ▼                 │
│  ┌──────────────┐  ┌──────────────┐        ┌──────────────────────┐    │
│  │  PostgreSQL  │  │    Redis     │        │     OpenAI / Claude   │    │
│  │  (Primary DB)│  │   (Cache &   │        │     LangChain / RAG   │    │
│  │  :5432       │  │    Queue)    │        │     External LLMs     │    │
│  └──────────────┘  │  :6379       │        └──────────────────────┘    │
│                    └──────────────┘                                     │
│          ┌──────────────────────────────────────────────────┐          │
│          ▼                  ▼                    ▼           ▼          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ ┌──────────┐   │
│  │    MinIO     │  │    Qdrant    │  │   Grafana    │ │Prometheus│   │
│  │  (S3-compat  │  │  (Vector DB) │  │  (Dashboards)│ │ (Metrics)│   │
│  │   Storage)   │  │  :6333       │  │  :3001       │ │  :9090   │   │
│  │  :9001       │  └──────────────┘  └──────────────┘ └──────────┘   │
│  └──────────────┘                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 What's Included

| # | Category | Workflows | Description |
|---|----------|-----------|-------------|
| 1 | 🧑‍💼 **HR Automation** | 12 | Resume screening, onboarding, payroll, PTO management |
| 2 | 💰 **CRM & Sales** | 14 | Lead scoring, pipeline automation, follow-up sequences |
| 3 | 📊 **Finance & Accounting** | 11 | Invoice processing, expense tracking, fraud detection |
| 4 | 🛠 **IT Operations** | 10 | Incident response, monitoring, deployment automation |
| 5 | 📣 **Marketing** | 12 | Campaign orchestration, social scheduling, SEO analysis |
| 6 | 🎧 **Customer Support** | 11 | Ticket triage, sentiment analysis, escalation routing |
| 7 | 📝 **Content Generation** | 10 | Blog writing, email drafting, product descriptions |
| 8 | 📦 **Supply Chain** | 10 | Inventory alerts, vendor management, order processing |
| 9 | 📈 **Analytics** | 10 | KPI dashboards, weekly reports, data pipeline triggers |
|   | **Total** | **100** | Full-company automation coverage |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.x
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.x
- Git

### 1. Clone & Configure

```bash
git clone https://github.com/your-org/ai-automation-platform.git
cd WEEK_5

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env   # or code .env
```

### 2. Start All Services

```bash
docker-compose up -d
```

### 3. Verify Everything is Running

```bash
docker-compose ps
curl http://localhost:8000/health
```

### 4. Import n8n Workflows

```bash
bash scripts/import_workflows.sh
```

### 5. Access the Platform

Open your browser at **http://localhost:3000** 🎉

> 💡 Use the automated setup script instead: `bash scripts/setup.sh`

---

## 🖥 Services

| Service | URL | Default Credentials | Description |
|---------|-----|---------------------|-------------|
| 📊 Dashboard | http://localhost:3000 | — | React frontend overview |
| 🔧 n8n | http://localhost:5678 | `admin` / `admin123` | Workflow automation engine |
| 🚀 FastAPI | http://localhost:8000 | — | AI backend REST API |
| 📖 API Docs | http://localhost:8000/docs | — | Interactive Swagger UI |
| 📚 ReDoc | http://localhost:8000/redoc | — | Alternative API docs |
| 🗄️ MinIO | http://localhost:9001 | `minioadmin` / `minioadmin123` | S3-compatible object storage |
| 📈 Grafana | http://localhost:3001 | `admin` / `admin` | Monitoring dashboards |
| 📡 Prometheus | http://localhost:9090 | — | Metrics collection |
| 🔍 Qdrant | http://localhost:6333 | — | Vector database UI |

---

## 🔌 API Endpoints

### 🧑‍💼 HR Automation (`/hr`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/hr/screen-resume` | AI-powered resume screening & scoring |
| `POST` | `/hr/generate-onboarding` | Generate onboarding checklist |
| `POST` | `/hr/analyze-sentiment` | Employee sentiment analysis |
| `GET` | `/hr/workforce-analytics` | Workforce metrics dashboard data |

### 💰 CRM & Sales (`/crm`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/crm/score-lead` | AI lead scoring (0–100) |
| `POST` | `/crm/draft-followup` | Generate follow-up email |
| `GET` | `/crm/pipeline-health` | Pipeline analytics snapshot |
| `POST` | `/crm/predict-churn` | Customer churn prediction |

### 📊 Finance (`/finance` & `/invoice`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/invoice/extract` | Extract data from invoice text/image |
| `POST` | `/finance/detect-fraud` | Anomaly & fraud detection |
| `GET` | `/finance/cash-flow` | Cash flow projection |
| `POST` | `/finance/categorize-expense` | AI expense categorization |

### 🎧 Customer Support (`/support`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/support/classify` | Classify & prioritize ticket |
| `POST` | `/support/draft-response` | AI-drafted support reply |
| `POST` | `/support/sentiment` | Customer sentiment scoring |
| `GET` | `/support/analytics` | Support metrics & SLA data |

### 📣 Marketing (`/marketing`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/marketing/generate-campaign` | AI campaign content generation |
| `POST` | `/marketing/social-post` | Social media post creation |
| `POST` | `/marketing/seo-analyze` | SEO keyword & content analysis |
| `GET` | `/marketing/campaign-metrics` | Campaign performance data |

### 📝 Content (`/content`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/content/blog-post` | Long-form blog article generation |
| `POST` | `/content/email-draft` | Professional email drafting |
| `POST` | `/content/product-description` | E-commerce product copy |
| `POST` | `/content/summarize` | Document/text summarization |

### 🛠 IT Operations (`/ops`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ops/incident-classify` | Incident classification & routing |
| `POST` | `/ops/runbook-generate` | Auto-generate runbook from incident |
| `GET` | `/ops/system-health` | Infrastructure health snapshot |

### 📦 Supply Chain (`/supply`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/supply/reorder-predict` | Predict when to reorder stock |
| `POST` | `/supply/vendor-score` | Score vendor performance |
| `GET` | `/supply/inventory-status` | Real-time inventory overview |

### 📈 Analytics (`/analytics`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/kpi-summary` | Company-wide KPI summary |
| `POST` | `/analytics/generate-report` | Trigger AI report generation |
| `GET` | `/analytics/trends` | Trend detection & insights |

### 🩺 System

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/` | Platform info & version |
| `GET` | `/metrics` | Prometheus metrics endpoint |

---

## 📥 Workflow Importing

### Method 1: Automated Script (Recommended)

```bash
bash scripts/import_workflows.sh
```

This script will import all 100 JSON workflows into n8n via the REST API.

### Method 2: Manual Import via UI

1. Open n8n at **http://localhost:5678**
2. Log in with `admin` / `admin123`
3. Click **"+"** → **"Import from File"**
4. Select any `.json` file from the `workflows/` directory
5. Click **"Import"** and **"Save"**

### Method 3: n8n CLI (Inside Container)

```bash
docker exec -it week5_n8n_1 n8n import:workflow --input=/home/node/workflows/
```

### Workflow Directory Structure

```
workflows/
├── hr/                    # 12 HR workflows
├── crm/                   # 14 CRM & Sales workflows
├── finance/               # 11 Finance workflows
├── it_operations/         # 10 IT Ops workflows
├── marketing/             # 12 Marketing workflows
├── customer_support/      # 11 Support workflows
├── content/               # 10 Content workflows
├── supply_chain/          # 10 Supply Chain workflows
└── analytics/             # 10 Analytics workflows
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in the values below.

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | OpenAI GPT-4 API key |
| `ANTHROPIC_API_KEY` | ⬜ | Claude API key (optional fallback) |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `MINIO_ENDPOINT` | ✅ | MinIO server endpoint |
| `MINIO_ACCESS_KEY` | ✅ | MinIO access key |
| `MINIO_SECRET_KEY` | ✅ | MinIO secret key |
| `QDRANT_URL` | ✅ | Qdrant vector DB URL |
| `N8N_BASIC_AUTH_USER` | ✅ | n8n admin username |
| `N8N_BASIC_AUTH_PASSWORD` | ✅ | n8n admin password |
| `SECRET_KEY` | ✅ | FastAPI JWT secret (generate with `openssl rand -hex 32`) |
| `SMTP_HOST` | ⬜ | SMTP host for email notifications |
| `SMTP_PORT` | ⬜ | SMTP port (default: 587) |
| `SMTP_USER` | ⬜ | SMTP username |
| `SMTP_PASSWORD` | ⬜ | SMTP password |
| `SLACK_WEBHOOK_URL` | ⬜ | Slack webhook for alerts |
| `ENVIRONMENT` | ✅ | `development` or `production` |
| `LOG_LEVEL` | ⬜ | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

---

## 🛠 Development

### Run Backend Locally (Without Docker)

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start only infrastructure services
docker-compose up -d postgres redis qdrant minio

# Run the FastAPI dev server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
cd backend
pytest tests/ -v --tb=short
```

### Code Quality

```bash
cd backend
ruff check .          # Linting
ruff format .         # Formatting
pyright .             # Type checking
```

### Hot-Reload Docker Development

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Orchestration** | n8n | Visual workflow automation |
| **API Backend** | FastAPI (Python 3.12) | REST API, AI logic |
| **AI / LLM** | OpenAI GPT-4o, Claude 3.5 | Language model calls |
| **AI Framework** | LangChain | Chains, RAG, agents |
| **Primary DB** | PostgreSQL 16 | Relational data |
| **Cache / Queue** | Redis 7 | Caching, task queuing |
| **Vector DB** | Qdrant | Embeddings & semantic search |
| **Object Storage** | MinIO | S3-compatible file storage |
| **Monitoring** | Prometheus + Grafana | Metrics & dashboards |
| **Frontend** | React + Vite | Dashboard UI |
| **Container** | Docker + Compose | Service orchestration |
| **CI/CD** | GitHub Actions | Automated testing & builds |
| **Linting** | Ruff | Fast Python linter |
| **Type Checking** | Pyright | Static type analysis |

---

## 🎓 Week 5 Bootcamp Context

This project is the **Week 5 capstone** of the AI Automation Bootcamp. The goal was to build a **production-grade, full-company automation platform** that demonstrates mastery of:

- 🔗 **Workflow Automation** — 100 n8n workflows covering every business department
- 🤖 **AI Integration** — GPT-4 and Claude for intelligent processing at every layer
- 🏗 **System Design** — Microservice architecture with proper separation of concerns
- 🐳 **DevOps** — Fully dockerised platform with CI/CD via GitHub Actions
- 📊 **Observability** — Prometheus metrics, Grafana dashboards, structured logging
- 🔒 **Security** — Auth middleware, secret management, network isolation
- 📝 **Documentation** — Comprehensive docs, ADRs, and API reference

### Learning Objectives Met

- [x] Design and deploy a multi-service Docker architecture
- [x] Build an AI-powered REST API with FastAPI
- [x] Create 100+ n8n automation workflows across 9 business domains
- [x] Integrate vector search (RAG) with Qdrant
- [x] Implement monitoring and alerting pipelines
- [x] Write CI/CD pipelines with automated testing

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. Create a **feature branch**: `git checkout -b feature/my-new-workflow`
3. **Commit** your changes: `git commit -m 'feat: add invoice OCR workflow'`
4. **Push** to the branch: `git push origin feature/my-new-workflow`
5. Open a **Pull Request** against `develop`

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use For |
|--------|---------|
| `feat:` | New workflow or feature |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `chore:` | Dependency updates, config |
| `test:` | Test additions or fixes |

### Code Standards

- Python: **Ruff** for linting, **Pyright** for types
- All new endpoints must have **docstrings** and **Pydantic models**
- n8n workflows must be **exported as JSON** and placed in the correct `workflows/` subdirectory

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 AI Automation Bootcamp — Week 5

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

<div align="center">

**Built with ❤️ during the AI Automation Bootcamp — Week 5**

[🐛 Report Bug](https://github.com/your-org/ai-automation-platform/issues) · [💡 Request Feature](https://github.com/your-org/ai-automation-platform/issues) · [📖 Docs](ARCHITECTURE.md)

</div>
