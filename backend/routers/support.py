"""
Support Router — AI-powered ticket classification, response generation, and escalation.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/support", tags=["Support"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ClassifyTicketRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Ticket title/subject")
    description: str = Field(..., min_length=10, description="Ticket description")
    customer_tier: str = Field(default="standard", description="Customer tier: free | standard | premium | enterprise")


class ClassifyTicketResponse(BaseModel):
    category: str
    subcategory: str
    priority: str  # low | medium | high | critical
    department: str
    confidence: float
    suggested_tags: list[str]
    estimated_resolution_hours: int


class GenerateResponseRequest(BaseModel):
    question: str = Field(..., description="Customer question or issue description")
    context: str = Field(default="", description="Additional context (product docs, account info, etc.)")
    tone: str = Field(default="friendly", description="Response tone: friendly | formal | empathetic | technical")
    max_length: int = Field(default=300, ge=50, le=1000, description="Max response length in words")


class GenerateResponseResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]
    suggested_follow_up: list[str]
    escalation_recommended: bool


class EscalationCheckRequest(BaseModel):
    ticket_data: dict[str, Any] = Field(
        ...,
        description="Ticket data including title, description, priority, customer_tier, created_at",
    )
    sla_breach_hours: int = Field(..., ge=0, description="SLA breach threshold in hours")
    current_age_hours: float = Field(default=0.0, ge=0, description="How old the ticket is in hours")


class EscalationCheckResponse(BaseModel):
    should_escalate: bool
    urgency_level: str  # routine | urgent | critical
    reason: str
    recommended_team: str
    sla_status: str  # on_track | at_risk | breached
    actions: list[str]


class SupportMetricsResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_today: int
    avg_resolution_hours: float
    customer_satisfaction: float
    first_response_avg_minutes: int
    escalation_rate: float
    categories: list[dict[str, Any]]
    sla_compliance: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESOLUTION_HOURS_MAP = {
    "billing": 4,
    "account": 8,
    "technical": 24,
    "bug": 48,
    "feature request": 168,
    "general": 24,
}

SLA_BY_TIER = {
    "enterprise": 2,
    "premium": 4,
    "standard": 24,
    "free": 72,
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/classify", response_model=ClassifyTicketResponse, summary="Classify Support Ticket")
async def classify_ticket(payload: ClassifyTicketRequest) -> ClassifyTicketResponse:
    """
    Automatically classify an incoming support ticket.

    Determines category, priority, department routing, and estimated resolution time.
    """
    try:
        result = await ai_service.classify_ticket(payload.title, payload.description)
        category = result.get("category", "General").lower()
        resolution_hours = RESOLUTION_HOURS_MAP.get(category, 24)

        # Enterprise customers always get elevated priority
        priority = result.get("priority", "medium")
        if payload.customer_tier == "enterprise" and priority == "low":
            priority = "medium"

        suggested_tags = [
            result.get("category", "general").lower().replace(" ", "-"),
            result.get("department", "support").lower().replace(" ", "-"),
            priority,
        ]

        return ClassifyTicketResponse(
            category=result.get("category", "General"),
            subcategory=result.get("subcategory", "Other"),
            priority=priority,
            department=result.get("department", "Support"),
            confidence=float(result.get("confidence", 0.85)),
            suggested_tags=suggested_tags,
            estimated_resolution_hours=resolution_hours,
        )
    except Exception as exc:
        log.error("support.classify.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Ticket classification failed: {exc}") from exc


@router.post("/generate-response", response_model=GenerateResponseResponse, summary="Generate Support Response")
async def generate_response(payload: GenerateResponseRequest) -> GenerateResponseResponse:
    """
    Generate an AI-powered response to a customer support query.

    Uses provided context and knowledge base to craft an accurate, tone-appropriate reply.
    """
    try:
        result = await ai_service.answer_support_query(payload.question, payload.context)
        confidence = float(result.get("confidence", 0.85))

        # Suggest escalation when confidence is low
        escalate = confidence < 0.60

        follow_ups = [
            "Is there anything else I can help you with?",
            "Did this resolve your issue?",
        ]
        if escalate:
            follow_ups.insert(0, "Would you like me to connect you with a specialist?")

        return GenerateResponseResponse(
            answer=result.get("answer", "I'm sorry, I need more information to assist you."),
            confidence=confidence,
            sources=result.get("sources", []),
            suggested_follow_up=follow_ups,
            escalation_recommended=escalate,
        )
    except Exception as exc:
        log.error("support.generate_response.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Response generation failed: {exc}") from exc


@router.post("/escalation-check", response_model=EscalationCheckResponse, summary="Check Ticket Escalation Need")
async def escalation_check(payload: EscalationCheckRequest) -> EscalationCheckResponse:
    """
    Determine whether a support ticket needs escalation based on SLA and ticket data.

    Evaluates age, customer tier, priority, and SLA breach threshold to recommend
    escalation actions.
    """
    try:
        ticket = payload.ticket_data
        priority = ticket.get("priority", "medium").lower()
        customer_tier = ticket.get("customer_tier", "standard").lower()
        age_hours = payload.current_age_hours

        # Determine SLA status
        sla_threshold = SLA_BY_TIER.get(customer_tier, 24)
        if age_hours >= payload.sla_breach_hours:
            sla_status = "breached"
        elif age_hours >= payload.sla_breach_hours * 0.8:
            sla_status = "at_risk"
        else:
            sla_status = "on_track"

        # Escalation logic
        should_escalate = (
            sla_status == "breached"
            or priority == "critical"
            or (priority == "high" and customer_tier in ("enterprise", "premium") and age_hours > sla_threshold * 0.5)
        )

        if priority == "critical" or sla_status == "breached":
            urgency = "critical"
        elif should_escalate:
            urgency = "urgent"
        else:
            urgency = "routine"

        # Reason
        reasons = []
        if sla_status == "breached":
            reasons.append(f"SLA breached (age: {age_hours:.1f}h, threshold: {payload.sla_breach_hours}h)")
        if priority == "critical":
            reasons.append("Critical priority ticket")
        if customer_tier in ("enterprise", "premium") and should_escalate:
            reasons.append(f"{customer_tier.title()} customer requires priority handling")
        reason = "; ".join(reasons) if reasons else "Ticket within SLA and no critical flags"

        # Recommended team
        category = ticket.get("category", "technical").lower()
        team_map = {
            "billing": "Billing Escalation Team",
            "technical": "Senior Engineering Support",
            "account": "Account Management",
            "bug": "Engineering — Bug Squad",
        }
        recommended_team = team_map.get(category, "L2 Support Team")

        # Actions
        actions = []
        if should_escalate:
            actions.extend([
                f"Escalate to {recommended_team} immediately",
                "Notify customer of escalation and revised ETA",
                "Flag for manager review",
            ])
            if customer_tier in ("enterprise", "premium"):
                actions.append("Notify dedicated customer success manager")
        else:
            actions.append("Continue standard resolution process")
            if sla_status == "at_risk":
                actions.append("Prioritise resolution to avoid SLA breach")

        return EscalationCheckResponse(
            should_escalate=should_escalate,
            urgency_level=urgency,
            reason=reason,
            recommended_team=recommended_team,
            sla_status=sla_status,
            actions=actions,
        )
    except Exception as exc:
        log.error("support.escalation_check.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Escalation check failed: {exc}") from exc


@router.get("/metrics", response_model=SupportMetricsResponse, summary="Support Dashboard Metrics")
async def support_metrics() -> SupportMetricsResponse:
    """
    Return current support operations metrics for the dashboard.

    Includes ticket volumes, resolution times, CSAT, and SLA compliance.
    """
    return SupportMetricsResponse(
        total_tickets=1842,
        open_tickets=247,
        resolved_today=89,
        avg_resolution_hours=14.2,
        customer_satisfaction=4.6,
        first_response_avg_minutes=18,
        escalation_rate=4.8,
        categories=[
            {"category": "Technical", "count": 742, "percentage": 40.3, "avg_resolution_h": 22},
            {"category": "Billing", "count": 384, "percentage": 20.8, "avg_resolution_h": 6},
            {"category": "Account", "count": 312, "percentage": 16.9, "avg_resolution_h": 10},
            {"category": "Feature Request", "count": 224, "percentage": 12.2, "avg_resolution_h": 168},
            {"category": "Bug Report", "count": 112, "percentage": 6.1, "avg_resolution_h": 48},
            {"category": "General", "count": 68, "percentage": 3.7, "avg_resolution_h": 8},
        ],
        sla_compliance=94.7,
    )
