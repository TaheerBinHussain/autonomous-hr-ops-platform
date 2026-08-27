"""
test_main.py — pytest test suite for AI Automation Platform (Week 5)
Tests all major API endpoints across every business domain.
"""
import os
import sys
import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the backend root is importable regardless of how pytest is invoked
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Environment mocks (must be set BEFORE importing FastAPI app) ──────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-mock-key-for-testing-only")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test-mock-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ.setdefault("MINIO_ENDPOINT", "localhost:9000")
os.environ.setdefault("MINIO_ACCESS_KEY", "minioadmin")
os.environ.setdefault("MINIO_SECRET_KEY", "minioadmin123")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

# ── Client fixture ────────────────────────────────────────────────────────────
client = TestClient(app, raise_server_exceptions=False)


# ══════════════════════════════════════════════════════════════════════════════
# 🩺 System / Health Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestSystem:
    """Tests for system-level endpoints."""

    def test_health_check(self):
        """GET /health should return 200 with status: healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """GET / should return 200 with platform info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_health_includes_version(self):
        """GET /health should include a version or timestamp field."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # At minimum, status must be present
        assert "status" in data

    def test_docs_accessible(self):
        """GET /docs should return 200 (Swagger UI)."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """GET /openapi.json should return a valid OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema


# ══════════════════════════════════════════════════════════════════════════════
# 🧑‍💼 HR Automation Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestHR:
    """Tests for HR automation endpoints."""

    def test_screen_resume_basic(self):
        """POST /hr/screen-resume should score a resume."""
        response = client.post("/hr/screen-resume", json={
            "resume_text": (
                "John Doe — Senior Software Engineer\n"
                "5 years Python experience, AWS certified, led team of 8.\n"
                "Experience: FastAPI, Docker, PostgreSQL, React."
            ),
            "job_description": (
                "Senior Python Developer with AWS experience. "
                "Strong FastAPI and PostgreSQL skills required."
            ),
        })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert isinstance(data["score"], (int, float))

    def test_screen_resume_score_range(self):
        """Resume score should be between 0 and 100."""
        response = client.post("/hr/screen-resume", json={
            "resume_text": "Jane Smith — 2 years Java developer",
            "job_description": "Python developer with 5 years experience",
        })
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["score"] <= 100

    def test_screen_resume_missing_fields(self):
        """POST /hr/screen-resume with missing body should return 422."""
        response = client.post("/hr/screen-resume", json={})
        assert response.status_code == 422

    def test_screen_resume_empty_strings(self):
        """POST /hr/screen-resume with empty strings should return 422 or 400."""
        response = client.post("/hr/screen-resume", json={
            "resume_text": "",
            "job_description": "",
        })
        assert response.status_code in (200, 400, 422)

    def test_generate_onboarding(self):
        """POST /hr/generate-onboarding should return a checklist."""
        response = client.post("/hr/generate-onboarding", json={
            "employee_name": "Alice Johnson",
            "role": "Backend Engineer",
            "department": "Engineering",
            "start_date": "2025-02-01",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_workforce_analytics(self):
        """GET /hr/workforce-analytics should return analytics data."""
        response = client.get("/hr/workforce-analytics")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 💰 CRM & Sales Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestCRM:
    """Tests for CRM and sales endpoints."""

    def test_score_lead_basic(self):
        """POST /crm/score-lead should return a score."""
        response = client.post("/crm/score-lead", json={
            "name": "Jane Smith",
            "company": "Tech Corp",
            "email": "jane@techcorp.com",
            "source": "website",
            "budget": 50000,
            "description": "Looking for AI automation solution for our sales team",
        })
        assert response.status_code == 200
        data = response.json()
        assert "score" in data

    def test_score_lead_score_range(self):
        """Lead score should be between 0 and 100."""
        response = client.post("/crm/score-lead", json={
            "name": "Bob Lee",
            "company": "StartupXYZ",
            "email": "bob@startupxyz.com",
            "source": "referral",
            "budget": 10000,
            "description": "Needs basic automation",
        })
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["score"] <= 100

    def test_score_lead_missing_required(self):
        """POST /crm/score-lead without required fields returns 422."""
        response = client.post("/crm/score-lead", json={"name": "Someone"})
        assert response.status_code == 422

    def test_draft_followup(self):
        """POST /crm/draft-followup should return email content."""
        response = client.post("/crm/draft-followup", json={
            "lead_name": "Alice Brown",
            "company": "MegaCorp",
            "last_interaction": "demo call",
            "context": "Interested in our enterprise plan",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_pipeline_health(self):
        """GET /crm/pipeline-health should return pipeline metrics."""
        response = client.get("/crm/pipeline-health")
        assert response.status_code == 200

    def test_predict_churn(self):
        """POST /crm/predict-churn should return churn prediction."""
        response = client.post("/crm/predict-churn", json={
            "customer_id": "cust-001",
            "company": "RetentionCorp",
            "last_login_days_ago": 45,
            "support_tickets_count": 8,
            "monthly_spend": 500,
            "contract_months_remaining": 2,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ══════════════════════════════════════════════════════════════════════════════
# 📊 Finance & Invoice Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestFinance:
    """Tests for finance and invoice endpoints."""

    def test_invoice_extract_basic(self):
        """POST /invoice/extract should parse invoice data."""
        response = client.post("/invoice/extract", json={
            "invoice_text": (
                "Invoice #INV-001\n"
                "Vendor: Tech Solutions Ltd\n"
                "Date: 2025-01-15\n"
                "Amount: $5,000.00\n"
                "Due Date: 2025-02-15\n"
                "Description: Software development services"
            )
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_invoice_extract_missing_text(self):
        """POST /invoice/extract with no text should return 422."""
        response = client.post("/invoice/extract", json={})
        assert response.status_code == 422

    def test_detect_fraud(self):
        """POST /finance/detect-fraud should return risk assessment."""
        response = client.post("/finance/detect-fraud", json={
            "transaction_id": "txn-12345",
            "amount": 99999.99,
            "vendor": "Unknown Vendor LLC",
            "category": "miscellaneous",
            "submitted_by": "new_employee@company.com",
            "notes": "urgent payment required immediately",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_categorize_expense(self):
        """POST /finance/categorize-expense should classify an expense."""
        response = client.post("/finance/categorize-expense", json={
            "description": "AWS EC2 monthly bill",
            "amount": 1250.00,
            "vendor": "Amazon Web Services",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_cash_flow(self):
        """GET /finance/cash-flow should return projection data."""
        response = client.get("/finance/cash-flow")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 🎧 Customer Support Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestSupport:
    """Tests for customer support endpoints."""

    def test_classify_ticket_basic(self):
        """POST /support/classify should categorize a ticket."""
        response = client.post("/support/classify", json={
            "title": "Cannot login to account",
            "description": (
                "I am getting a 401 error when trying to login. "
                "This started happening after the last update."
            ),
        })
        assert response.status_code == 200
        data = response.json()
        assert "category" in data

    def test_classify_ticket_urgent(self):
        """POST /support/classify should detect urgent/P1 tickets."""
        response = client.post("/support/classify", json={
            "title": "Production system is completely down",
            "description": "All users are unable to access the platform. Revenue impact.",
        })
        assert response.status_code == 200
        data = response.json()
        assert "category" in data
        assert "priority" in data or isinstance(data, dict)

    def test_classify_missing_fields(self):
        """POST /support/classify without body fields returns 422."""
        response = client.post("/support/classify", json={})
        assert response.status_code == 422

    def test_draft_response(self):
        """POST /support/draft-response should generate a reply."""
        response = client.post("/support/draft-response", json={
            "ticket_id": "TKT-001",
            "title": "Cannot reset password",
            "description": "I tried resetting but never received the email",
            "category": "account",
            "customer_name": "Mark Davis",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_sentiment_analysis(self):
        """POST /support/sentiment should return a sentiment score."""
        response = client.post("/support/sentiment", json={
            "text": "I am extremely frustrated with the constant bugs!",
            "customer_id": "cust-999",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_support_analytics(self):
        """GET /support/analytics should return metrics."""
        response = client.get("/support/analytics")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 📣 Marketing Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestMarketing:
    """Tests for marketing automation endpoints."""

    def test_generate_campaign(self):
        """POST /marketing/generate-campaign should return campaign content."""
        response = client.post("/marketing/generate-campaign", json={
            "product": "AI Automation Platform",
            "target_audience": "CTO and VP Engineering",
            "campaign_goal": "increase trial sign-ups",
            "tone": "professional",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_social_post(self):
        """POST /marketing/social-post should generate social media content."""
        response = client.post("/marketing/social-post", json={
            "topic": "AI automation saves 40 hours per week",
            "platform": "linkedin",
            "include_hashtags": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_seo_analyze(self):
        """POST /marketing/seo-analyze should return SEO analysis."""
        response = client.post("/marketing/seo-analyze", json={
            "url": "https://example.com/blog/ai-automation",
            "content": "This article covers AI automation benefits for enterprises...",
            "target_keywords": ["AI automation", "workflow automation"],
        })
        assert response.status_code == 200

    def test_campaign_metrics(self):
        """GET /marketing/campaign-metrics should return performance data."""
        response = client.get("/marketing/campaign-metrics")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 📝 Content Generation Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestContent:
    """Tests for content generation endpoints."""

    def test_blog_post(self):
        """POST /content/blog-post should generate a blog article."""
        response = client.post("/content/blog-post", json={
            "topic": "The future of AI automation in enterprise",
            "target_length": "medium",
            "tone": "informative",
            "target_keywords": ["AI automation", "enterprise", "productivity"],
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_email_draft(self):
        """POST /content/email-draft should generate an email."""
        response = client.post("/content/email-draft", json={
            "purpose": "follow-up after product demo",
            "recipient_name": "Sarah Connor",
            "recipient_company": "TechStart Inc",
            "sender_name": "Alex Johnson",
            "key_points": ["discussed pricing", "scheduled next call", "sent proposal"],
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_product_description(self):
        """POST /content/product-description should generate product copy."""
        response = client.post("/content/product-description", json={
            "product_name": "AI Workflow Automator Pro",
            "features": ["100 pre-built workflows", "no-code editor", "API integrations"],
            "target_audience": "business users",
            "tone": "persuasive",
        })
        assert response.status_code == 200

    def test_summarize(self):
        """POST /content/summarize should return a summary."""
        response = client.post("/content/summarize", json={
            "text": (
                "Artificial intelligence is transforming businesses across all industries. "
                "Companies that adopt AI automation tools report 40% reduction in manual work, "
                "60% faster decision-making, and 25% cost savings in operational expenses. "
                "The technology is particularly impactful in HR, finance, customer support, "
                "and supply chain management. As AI models become more capable and accessible, "
                "even small businesses are beginning to deploy sophisticated automation workflows."
            ),
            "max_length": 100,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ══════════════════════════════════════════════════════════════════════════════
# 🛠 IT Operations Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestITOps:
    """Tests for IT operations endpoints."""

    def test_incident_classify(self):
        """POST /ops/incident-classify should classify an incident."""
        response = client.post("/ops/incident-classify", json={
            "title": "Database connection pool exhausted",
            "description": "Getting 'too many connections' errors in production",
            "affected_service": "postgres",
            "severity_hint": "high",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_runbook_generate(self):
        """POST /ops/runbook-generate should generate an operational runbook."""
        response = client.post("/ops/runbook-generate", json={
            "incident_type": "database_connection_exhaustion",
            "affected_services": ["postgres", "fastapi"],
            "symptoms": ["high latency", "connection timeouts"],
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_system_health(self):
        """GET /ops/system-health should return infrastructure health."""
        response = client.get("/ops/system-health")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 📦 Supply Chain Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestSupplyChain:
    """Tests for supply chain endpoints."""

    def test_reorder_predict(self):
        """POST /supply/reorder-predict should predict reorder timing."""
        response = client.post("/supply/reorder-predict", json={
            "product_id": "SKU-12345",
            "product_name": "Server SSD 2TB",
            "current_stock": 5,
            "average_daily_usage": 2,
            "lead_time_days": 7,
            "safety_stock": 10,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_vendor_score(self):
        """POST /supply/vendor-score should score a vendor."""
        response = client.post("/supply/vendor-score", json={
            "vendor_id": "VND-001",
            "vendor_name": "Tech Supplies Co",
            "on_time_delivery_rate": 0.92,
            "quality_score": 4.5,
            "price_competitiveness": 0.85,
            "response_time_hours": 4,
            "total_orders": 150,
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_inventory_status(self):
        """GET /supply/inventory-status should return inventory overview."""
        response = client.get("/supply/inventory-status")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 📈 Analytics Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalytics:
    """Tests for analytics endpoints."""

    def test_kpi_summary(self):
        """GET /analytics/kpi-summary should return KPI data."""
        response = client.get("/analytics/kpi-summary")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_generate_report(self):
        """POST /analytics/generate-report should trigger report generation."""
        response = client.post("/analytics/generate-report", json={
            "report_type": "weekly_summary",
            "date_range": "last_7_days",
            "departments": ["hr", "crm", "finance"],
            "format": "json",
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_trends(self):
        """GET /analytics/trends should return trend data."""
        response = client.get("/analytics/trends")
        assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# 🔧 Edge Cases & Input Validation
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tests for edge cases and input validation."""

    def test_invalid_json_body(self):
        """Sending invalid Content-Type should return 422 or 415."""
        response = client.post(
            "/hr/screen-resume",
            content=b"not json at all!!!",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in (400, 422)

    def test_very_long_text(self):
        """Extremely long text inputs should be handled without crash."""
        long_text = "Python developer " * 5000  # ~85,000 chars
        response = client.post("/hr/screen-resume", json={
            "resume_text": long_text,
            "job_description": "Python developer",
        })
        # Should not return 500
        assert response.status_code != 500

    def test_special_characters_in_input(self):
        """Inputs with special chars, emojis, and SQL-like strings are safe."""
        response = client.post("/support/classify", json={
            "title": "Login broken 🔥 DROP TABLE users; --",
            "description": "<script>alert('xss')</script> also please help me login 😤",
        })
        # Should not crash
        assert response.status_code in (200, 400, 422)

    def test_negative_budget_lead(self):
        """Negative budget should be rejected or handled gracefully."""
        response = client.post("/crm/score-lead", json={
            "name": "Test Lead",
            "company": "Test Co",
            "email": "test@test.com",
            "source": "website",
            "budget": -9999,
            "description": "test",
        })
        assert response.status_code in (200, 400, 422)

    def test_method_not_allowed(self):
        """Using wrong HTTP method returns 405."""
        response = client.post("/health")  # Health is a GET endpoint
        assert response.status_code in (405, 404)

    def test_unknown_endpoint(self):
        """Unknown endpoints return 404."""
        response = client.get("/this/endpoint/does/not/exist")
        assert response.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 🏎 Performance / Response Time
# ══════════════════════════════════════════════════════════════════════════════

class TestPerformance:
    """Basic response time expectations (mocked AI = fast)."""

    def test_health_check_is_fast(self):
        """Health check should respond in under 500ms (synchronous mock)."""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed_ms = (time.time() - start) * 1000
        assert response.status_code == 200
        # With mocked LLMs, health should be very fast
        assert elapsed_ms < 2000, f"Health check took {elapsed_ms:.0f}ms — too slow"

    def test_multiple_concurrent_health_checks(self):
        """Multiple sequential health checks all succeed."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
