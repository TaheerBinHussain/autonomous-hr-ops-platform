"""
AI Service — wraps OpenAI calls with retry logic and mock fallback.

When OPENAI_API_KEY is empty the service returns realistic mock data so the
rest of the platform remains fully functional without a paid key.
"""

from __future__ import annotations

import json
import random
from typing import Any

import structlog
from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_mock() -> bool:
    """Return True when no real API key is configured or placeholder key is present."""
    key = settings.openai_api_key.strip()
    return not key or key.startswith("sk-your-") or "your-" in key or len(key) < 20


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class AIService:
    """Central AI service used by all domain routers."""

    def __init__(self) -> None:
        if not _is_mock():
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self._client = None  # type: ignore[assignment]
            log.warning("ai_service.mock_mode", reason="OPENAI_API_KEY not set")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
        response_format: dict | None = None,
    ) -> str:
        """Low-level chat completion with automatic retry."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = await self._client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful AI assistant.",
        model: str = "gpt-4o-mini",
        max_tokens: int = 2000,
    ) -> str:
        """General-purpose text completion."""
        if _is_mock():
            return f"[MOCK] Response to: {prompt[:80]}..."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        return await self._chat(messages, model=model, max_tokens=max_tokens)

    async def extract_structured(
        self, text: str, schema_description: str
    ) -> dict:
        """Extract structured JSON data from free text using JSON mode."""
        if _is_mock():
            return {"mock": True, "extracted": "sample data", "text_length": len(text)}

        system_prompt = (
            "You are a data extraction assistant. Always respond with valid JSON only. "
            f"Extract the following information: {schema_description}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        raw = await self._chat(
            messages,
            response_format={"type": "json_object"},
            max_tokens=2000,
        )
        return json.loads(raw)

    async def score_resume(
        self, resume_text: str, job_description: str
    ) -> dict:
        """Score a resume against a job description (0-100)."""
        if _is_mock():
            keywords = ["python", "fastapi", "docker", "kubernetes", "n8n", "openai", "ai", "engineer", "devops", "sql", "platform"]
            resume_lower = resume_text.lower()
            matches = sum(1 for kw in keywords if kw in resume_lower)
            if matches >= 3:
                score = min(78 + matches * 2, 98)
                return {
                    "score": score,
                    "strengths": [
                        "Extensive experience matching core technical stack",
                        "Proven expertise in Python, FastAPI, Docker, and AI platform engineering",
                        "Strong background in automated workflows and API architecture",
                    ],
                    "weaknesses": [
                        "High compensation expectation",
                    ],
                    "recommendation": "Strong Hire — Proceed to Offer Letter",
                }
            else:
                score = max(25 + matches * 4, 45)
                return {
                    "score": score,
                    "strengths": [
                        "Good general background",
                    ],
                    "weaknesses": [
                        "Lacks required technical stack (Python, FastAPI, Docker, n8n)",
                        "Insufficient engineering experience for AI Platform role",
                    ],
                    "recommendation": "Do Not Hire — Does not meet technical criteria",
                }

        system_prompt = (
            "You are an expert HR recruiter. Analyse the resume against the job description "
            "and return JSON with keys: score (int 0-100), strengths (list[str]), "
            "weaknesses (list[str]), recommendation (str)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Job Description:\n{job_description}\n\nResume:\n{resume_text}"
                ),
            },
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=1000
        )
        return json.loads(raw)

    async def generate_email(
        self, context: str, tone: str = "professional", purpose: str = "general"
    ) -> dict:
        """Generate an email with subject, plain body, and HTML body."""
        if _is_mock():
            return {
                "subject": f"[{purpose.title()}] Important Update",
                "body": (
                    f"Dear Recipient,\n\nThis is a {tone} email regarding {purpose}.\n\n"
                    f"Context: {context[:200]}\n\nBest regards,\nThe Team"
                ),
                "html_body": (
                    f"<p>Dear Recipient,</p><p>This is a <strong>{tone}</strong> email "
                    f"regarding <em>{purpose}</em>.</p><p>{context[:200]}</p>"
                    "<p>Best regards,<br>The Team</p>"
                ),
            }

        system_prompt = (
            "You are a professional email writer. Return JSON with keys: "
            "subject (str), body (str), html_body (str)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Write a {tone} email for the following purpose: {purpose}\n"
                    f"Context: {context}"
                ),
            },
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=1500
        )
        return json.loads(raw)

    async def classify_ticket(self, title: str, description: str) -> dict:
        """Classify a support ticket by category, priority, and department."""
        if _is_mock():
            categories = ["Technical", "Billing", "Account", "Feature Request", "Bug"]
            priorities = ["low", "medium", "high", "critical"]
            departments = ["Engineering", "Billing", "Customer Success", "Product"]
            return {
                "category": random.choice(categories),
                "priority": random.choice(priorities),
                "department": random.choice(departments),
                "confidence": round(random.uniform(0.75, 0.99), 2),
            }

        system_prompt = (
            "You are a support ticket classifier. Return JSON with keys: "
            "category (str), priority (low|medium|high|critical), "
            "department (str), confidence (float 0-1)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Title: {title}\nDescription: {description}",
            },
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=300
        )
        return json.loads(raw)

    async def generate_proposal_section(
        self, rfp_text: str, section: str, company_info: str
    ) -> str:
        """Generate a specific section of a business proposal."""
        if _is_mock():
            return (
                f"## {section}\n\n"
                "Our team brings extensive experience and proven methodologies to address "
                f"your requirements outlined in the RFP. {company_info[:100]} "
                "We are committed to delivering exceptional results within the agreed timeline. "
                "Our approach combines industry best practices with innovative solutions "
                "tailored specifically to your organisational needs.\n\n"
                "**Key highlights:**\n"
                "- Proven track record in similar projects\n"
                "- Dedicated project team\n"
                "- Transparent reporting and communication\n"
            )

        system_prompt = (
            "You are an expert proposal writer helping a company respond to an RFP. "
            "Write clear, compelling, professional content."
        )
        prompt = (
            f"RFP Excerpt:\n{rfp_text[:2000]}\n\n"
            f"Company Info:\n{company_info}\n\n"
            f"Write the '{section}' section of the proposal."
        )
        return await self.complete(prompt, system_prompt=system_prompt, max_tokens=1200)

    async def summarize_meeting(self, transcript: str) -> dict:
        """Summarise a meeting transcript into structured output."""
        if _is_mock():
            return {
                "summary": (
                    "The team discussed project progress, identified blockers, and aligned "
                    "on next steps. Key decisions were made regarding timeline and resource allocation."
                ),
                "action_items": [
                    "Alice to send updated project plan by Friday",
                    "Bob to schedule follow-up with the client",
                    "Carol to review and approve the budget proposal",
                ],
                "decisions": [
                    "Approved Q3 roadmap with minor adjustments",
                    "Agreed to defer feature X to next sprint",
                ],
                "next_steps": [
                    "Schedule weekly check-ins",
                    "Share meeting notes with stakeholders",
                    "Begin implementation phase on Monday",
                ],
            }

        system_prompt = (
            "You are an expert meeting analyst. Return JSON with keys: "
            "summary (str), action_items (list[str]), decisions (list[str]), next_steps (list[str])."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Meeting transcript:\n{transcript}"},
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=1500
        )
        return json.loads(raw)

    async def extract_invoice_data(self, text: str) -> dict:
        """Extract structured invoice data from raw text."""
        if _is_mock():
            return {
                "vendor": "Acme Corp",
                "amount": 4250.00,
                "currency": "USD",
                "date": "2026-08-01",
                "due_date": "2026-08-31",
                "invoice_number": "INV-2026-0842",
                "line_items": [
                    {"description": "Consulting Services", "quantity": 10, "unit_price": 350.00, "total": 3500.00},
                    {"description": "Software License", "quantity": 1, "unit_price": 750.00, "total": 750.00},
                ],
                "tax": 0.0,
                "subtotal": 4250.00,
            }

        schema = (
            "vendor, amount (float), currency, date (YYYY-MM-DD), due_date (YYYY-MM-DD), "
            "invoice_number, line_items (list of {description, quantity, unit_price, total}), "
            "tax (float), subtotal (float)"
        )
        return await self.extract_structured(text, schema)

    async def score_lead(self, lead_info: dict) -> dict:
        """Score a CRM lead and classify as hot/warm/cold."""
        if _is_mock():
            score = random.randint(30, 95)
            tier = "hot" if score >= 70 else ("warm" if score >= 45 else "cold")
            return {
                "score": score,
                "tier": tier,
                "reasoning": (
                    f"Lead shows {tier} engagement signals. "
                    "Budget aligns with product offering and decision timeline is clear."
                ),
                "recommended_action": (
                    "Schedule a demo call immediately."
                    if tier == "hot"
                    else "Add to nurture sequence." if tier == "warm"
                    else "Move to long-term nurture list."
                ),
            }

        system_prompt = (
            "You are a CRM analyst. Score this lead and return JSON with keys: "
            "score (int 0-100), tier (hot|warm|cold), reasoning (str), recommended_action (str)."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Lead info: {json.dumps(lead_info)}"},
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=500
        )
        return json.loads(raw)

    async def answer_support_query(
        self, question: str, context: str = ""
    ) -> dict:
        """Answer a support question using available context."""
        if _is_mock():
            return {
                "answer": (
                    f"Thank you for reaching out. Based on your question about '{question[:60]}', "
                    "here is our recommended solution: Please follow the standard troubleshooting steps "
                    "outlined in our help centre. If the issue persists, our technical team will escalate "
                    "this to the appropriate department within 24 hours."
                ),
                "confidence": round(random.uniform(0.70, 0.98), 2),
                "sources": ["Help Center Article #1042", "FAQ Section 3.2"],
            }

        system_prompt = (
            "You are a knowledgeable support agent. Answer the user's question clearly. "
            "Return JSON with keys: answer (str), confidence (float 0-1), sources (list[str])."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\nQuestion: {question}"
                    if context
                    else f"Question: {question}"
                ),
            },
        ]
        raw = await self._chat(
            messages, response_format={"type": "json_object"}, max_tokens=800
        )
        return json.loads(raw)


# Singleton instance used across routers
ai_service = AIService()
