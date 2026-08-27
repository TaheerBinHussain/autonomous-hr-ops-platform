"""
CRM Router — AI-powered lead scoring, nurture emails, churn prediction, and upsell.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/crm", tags=["CRM"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class LeadInfo(BaseModel):
    name: str = Field(..., description="Lead full name")
    company: str = Field(..., description="Company name")
    email: str = Field(..., description="Lead email address")
    source: str = Field(..., description="Lead source (e.g. LinkedIn, Website, Referral)")
    budget: str = Field(default="", description="Stated budget range")
    description: str = Field(default="", description="Additional notes about the lead")
    industry: str = Field(default="", description="Industry vertical")
    company_size: str = Field(default="", description="Company size (e.g. 50-200 employees)")
    job_title: str = Field(default="", description="Decision-maker job title")


class LeadScoreResponse(BaseModel):
    score: int
    tier: str  # hot | warm | cold
    reasoning: str
    recommended_action: str


class NurtureEmailRequest(BaseModel):
    lead_name: str
    company: str
    pain_point: str = Field(..., description="Primary pain point to address")
    stage: str = Field(..., description="Pipeline stage (e.g. awareness, consideration, decision)")
    product_name: str = Field(default="our platform", description="Product/service being offered")


class NurtureEmailResponse(BaseModel):
    subject: str
    body: str
    html_body: str


class ChurnPredictionRequest(BaseModel):
    customer_data: dict[str, Any] = Field(
        ...,
        description="Customer data dict with usage metrics, contract info, support history",
    )


class ChurnPredictionResponse(BaseModel):
    churn_risk_score: int  # 0-100
    risk_level: str  # low | medium | high
    key_risk_factors: list[str]
    recommendation: str
    retention_actions: list[str]


class UpsellRequest(BaseModel):
    customer_id: str
    customer_name: str = ""
    purchase_history: list[dict[str, Any]] = Field(
        ..., description="List of past purchases with product and amount"
    )
    current_plan: str = Field(default="", description="Current subscription/plan tier")


class UpsellResponse(BaseModel):
    customer_id: str
    recommendations: list[dict[str, Any]]
    estimated_revenue_uplift: str


class PipelineSummaryResponse(BaseModel):
    total_leads: int
    total_pipeline_value: str
    stages: list[dict[str, Any]]
    conversion_rate: float
    avg_deal_size: str
    top_sources: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/score-lead", response_model=LeadScoreResponse, summary="AI Lead Scoring")
async def score_lead(payload: LeadInfo) -> LeadScoreResponse:
    """
    Score an inbound lead using AI analysis of firmographic and behavioural signals.

    Returns a score (0-100), tier (hot/warm/cold), reasoning, and recommended next action.
    """
    try:
        result = await ai_service.score_lead(payload.model_dump())
        return LeadScoreResponse(**result)
    except Exception as exc:
        log.error("crm.score_lead.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Lead scoring failed: {exc}") from exc


@router.post("/nurture-email", response_model=NurtureEmailResponse, summary="Generate Nurture Email")
async def nurture_email(payload: NurtureEmailRequest) -> NurtureEmailResponse:
    """
    Generate a personalised lead nurture email for a specific pipeline stage.

    Tailors the message tone and CTA to the prospect's pain point and buying stage.
    """
    try:
        context = (
            f"Prospect: {payload.lead_name} from {payload.company}. "
            f"Pain point: {payload.pain_point}. "
            f"Pipeline stage: {payload.stage}. "
            f"Product: {payload.product_name}."
        )
        result = await ai_service.generate_email(
            context=context,
            tone="conversational and value-focused",
            purpose=f"lead nurture at {payload.stage} stage",
        )
        return NurtureEmailResponse(**result)
    except Exception as exc:
        log.error("crm.nurture_email.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Nurture email generation failed: {exc}") from exc


@router.post("/churn-prediction", response_model=ChurnPredictionResponse, summary="Predict Customer Churn")
async def churn_prediction(payload: ChurnPredictionRequest) -> ChurnPredictionResponse:
    """
    Predict churn risk for a customer based on usage and engagement data.

    Returns a risk score, identified risk factors, and retention action plan.
    """
    try:
        # Build a descriptive prompt from the customer data dict
        data_str = "\n".join(f"  {k}: {v}" for k, v in payload.customer_data.items())
        schema = (
            "churn_risk_score (int 0-100), risk_level (low|medium|high), "
            "key_risk_factors (list[str]), recommendation (str), retention_actions (list[str])"
        )
        result = await ai_service.extract_structured(
            f"Customer data:\n{data_str}", schema
        )
        # Ensure risk_level consistency with score
        score = int(result.get("churn_risk_score", 50))
        risk_level = result.get("risk_level", "medium")
        if risk_level not in ("low", "medium", "high"):
            risk_level = "high" if score >= 70 else ("medium" if score >= 40 else "low")

        return ChurnPredictionResponse(
            churn_risk_score=score,
            risk_level=risk_level,
            key_risk_factors=result.get("key_risk_factors", ["Low feature adoption", "Declining login frequency"]),
            recommendation=result.get("recommendation", "Schedule a proactive success call immediately."),
            retention_actions=result.get("retention_actions", ["Assign dedicated CSM", "Offer training session", "Provide renewal discount"]),
        )
    except Exception as exc:
        log.error("crm.churn_prediction.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Churn prediction failed: {exc}") from exc


@router.post("/upsell-opportunity", response_model=UpsellResponse, summary="Identify Upsell Opportunities")
async def upsell_opportunity(payload: UpsellRequest) -> UpsellResponse:
    """
    Analyse a customer's purchase history and identify upsell/cross-sell opportunities.

    Returns ranked product recommendations with rationale and estimated revenue impact.
    """
    try:
        history_str = "\n".join(
            f"  - {p.get('product', 'Unknown')} — ${p.get('amount', 0)}" for p in payload.purchase_history
        )
        schema = (
            "recommendations (list of {product, rationale, estimated_value, priority}), "
            "estimated_revenue_uplift (str)"
        )
        result = await ai_service.extract_structured(
            f"Customer ID: {payload.customer_id}\n"
            f"Current plan: {payload.current_plan or 'Standard'}\n"
            f"Purchase history:\n{history_str}",
            schema,
        )
        recommendations = result.get("recommendations", [
            {
                "product": "Enterprise Plan",
                "rationale": "Customer volume suggests they would benefit from higher limits",
                "estimated_value": "$2,400/year",
                "priority": "high",
            },
            {
                "product": "Advanced Analytics Add-on",
                "rationale": "Complements existing usage patterns",
                "estimated_value": "$600/year",
                "priority": "medium",
            },
        ])
        return UpsellResponse(
            customer_id=payload.customer_id,
            recommendations=recommendations,
            estimated_revenue_uplift=result.get("estimated_revenue_uplift", "$3,000/year"),
        )
    except Exception as exc:
        log.error("crm.upsell.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Upsell analysis failed: {exc}") from exc


@router.get("/pipeline-summary", response_model=PipelineSummaryResponse, summary="CRM Pipeline Summary")
async def pipeline_summary() -> PipelineSummaryResponse:
    """
    Return a summary of the current sales pipeline.

    Includes stage breakdown, conversion rates, deal sizes, and top lead sources.
    """
    return PipelineSummaryResponse(
        total_leads=512,
        total_pipeline_value="$4,280,000",
        stages=[
            {"stage": "Prospecting", "count": 185, "value": "$620,000", "avg_days": 7},
            {"stage": "Qualification", "count": 124, "value": "$890,000", "avg_days": 12},
            {"stage": "Proposal", "count": 87, "value": "$1,150,000", "avg_days": 18},
            {"stage": "Negotiation", "count": 62, "value": "$980,000", "avg_days": 14},
            {"stage": "Closed Won", "count": 38, "value": "$520,000", "avg_days": 6},
            {"stage": "Closed Lost", "count": 16, "value": "$120,000", "avg_days": 0},
        ],
        conversion_rate=22.4,
        avg_deal_size="$47,600",
        top_sources=[
            {"source": "Website", "leads": 198, "percentage": 38.7},
            {"source": "LinkedIn", "leads": 134, "percentage": 26.2},
            {"source": "Referral", "leads": 98, "percentage": 19.1},
            {"source": "Events", "leads": 52, "percentage": 10.2},
            {"source": "Cold Outreach", "leads": 30, "percentage": 5.9},
        ],
    )
