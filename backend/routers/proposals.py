"""
Proposals Router — AI-powered RFP parsing, section generation, and full proposal assembly.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/proposals", tags=["Proposals"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ParseRFPRequest(BaseModel):
    rfp_text: str = Field(..., min_length=100, description="Full RFP document text")


class ParseRFPResponse(BaseModel):
    title: str
    issuer: str
    deadline: str
    budget_range: str
    scope: str
    requirements: list[str]
    evaluation_criteria: list[str]
    submission_instructions: str
    key_dates: list[dict[str, str]]
    recommended_sections: list[str]


class GenerateSectionRequest(BaseModel):
    rfp_text: str = Field(..., description="RFP text for context")
    section_name: str = Field(..., description="Section to generate (e.g. 'Executive Summary', 'Technical Approach')")
    company_info: str = Field(..., description="Company background, capabilities, and differentiators")
    word_limit: int = Field(default=500, ge=100, le=2000)


class GenerateSectionResponse(BaseModel):
    section_name: str
    content: str
    word_count: int


class CompanyProfile(BaseModel):
    name: str
    tagline: str = ""
    description: str = ""
    founded_year: int = 2010
    team_size: str = ""
    key_clients: list[str] = []
    case_studies: list[str] = []
    certifications: list[str] = []
    contact_email: str = ""
    contact_phone: str = ""
    website: str = ""


class FullProposalRequest(BaseModel):
    rfp_text: str = Field(..., min_length=100, description="Full RFP document text")
    company_info: CompanyProfile
    sections: list[str] = Field(
        default=[
            "Executive Summary",
            "Understanding of Requirements",
            "Technical Approach",
            "Project Timeline",
            "Team and Qualifications",
            "Pricing",
            "References and Case Studies",
        ],
        description="List of sections to include in the proposal",
    )
    custom_instructions: str = Field(default="", description="Any additional instructions or emphasis")


class ProposalSection(BaseModel):
    section_name: str
    content: str
    word_count: int


class FullProposalResponse(BaseModel):
    title: str
    sections: list[ProposalSection]
    total_word_count: int
    html_proposal: str


class ProposalTemplate(BaseModel):
    id: str
    name: str
    description: str
    sections: list[str]
    suitable_for: list[str]
    estimated_pages: int


# ---------------------------------------------------------------------------
# Pre-defined templates
# ---------------------------------------------------------------------------

TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "software-development",
        "name": "Software Development Proposal",
        "description": "Comprehensive template for software development and IT projects",
        "sections": [
            "Executive Summary",
            "Understanding of Requirements",
            "Technical Approach & Architecture",
            "Development Methodology",
            "Project Timeline & Milestones",
            "Team Structure & Qualifications",
            "Quality Assurance",
            "Pricing & Payment Terms",
            "References & Case Studies",
            "Terms and Conditions",
        ],
        "suitable_for": ["Software Development", "IT Consulting", "Digital Transformation"],
        "estimated_pages": 20,
    },
    {
        "id": "consulting-services",
        "name": "Management Consulting Proposal",
        "description": "Template for management consulting and advisory service proposals",
        "sections": [
            "Executive Summary",
            "Problem Statement",
            "Proposed Solution & Methodology",
            "Deliverables",
            "Project Timeline",
            "Team Expertise",
            "Fee Structure",
            "Client References",
        ],
        "suitable_for": ["Management Consulting", "Strategy", "Organisational Change"],
        "estimated_pages": 15,
    },
    {
        "id": "marketing-services",
        "name": "Marketing & Creative Services Proposal",
        "description": "Template for marketing, branding, and creative services RFPs",
        "sections": [
            "Executive Summary",
            "Brand Understanding",
            "Creative Strategy",
            "Campaign Approach",
            "Content Plan",
            "Timeline & Deliverables",
            "Measurement & KPIs",
            "Agency Profile & Team",
            "Investment",
            "Portfolio Samples",
        ],
        "suitable_for": ["Marketing", "Branding", "Advertising", "PR"],
        "estimated_pages": 18,
    },
    {
        "id": "infrastructure",
        "name": "Infrastructure & Cloud Services Proposal",
        "description": "Template for cloud, hosting, and infrastructure projects",
        "sections": [
            "Executive Summary",
            "Infrastructure Assessment",
            "Proposed Architecture",
            "Security & Compliance",
            "Migration Strategy",
            "SLA & Support",
            "Pricing & Licensing",
            "Implementation Timeline",
            "Company Certifications",
        ],
        "suitable_for": ["Cloud Migration", "Infrastructure", "DevOps", "Security"],
        "estimated_pages": 22,
    },
    {
        "id": "training-services",
        "name": "Training & Learning Development Proposal",
        "description": "Template for corporate training and learning solutions",
        "sections": [
            "Executive Summary",
            "Training Needs Analysis",
            "Learning Objectives",
            "Curriculum Design",
            "Delivery Methodology",
            "Assessment & Evaluation",
            "Facilitator Profiles",
            "Investment & ROI",
        ],
        "suitable_for": ["Corporate Training", "L&D", "e-Learning"],
        "estimated_pages": 12,
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_html_proposal(
    title: str, company_name: str, sections: list[ProposalSection]
) -> str:
    section_html = "".join(
        f"<section style='margin-bottom:40px'>"
        f"<h2 style='color:#4f46e5;border-bottom:2px solid #e5e7eb;padding-bottom:8px'>{s.section_name}</h2>"
        f"<div style='line-height:1.7'>{s.content.replace(chr(10), '<br>')}</div>"
        f"</section>"
        for s in sections
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title>
<style>
  body{{font-family:'Segoe UI',Arial,sans-serif;max-width:900px;margin:0 auto;padding:40px;color:#1f2937}}
  .cover{{text-align:center;padding:60px 0;border-bottom:3px solid #4f46e5;margin-bottom:40px}}
  .cover h1{{font-size:2.2em;color:#4f46e5;margin-bottom:12px}}
  .cover p{{color:#6b7280;font-size:1.1em}}
  .toc{{background:#f9fafb;border-left:4px solid #4f46e5;padding:20px;margin-bottom:40px}}
  .toc h3{{margin-top:0;color:#4f46e5}}
  .toc ol{{margin:0;color:#374151}}
</style>
</head>
<body>
<div class="cover">
  <h1>{title}</h1>
  <p>Prepared by <strong>{company_name}</strong></p>
</div>
<div class="toc">
  <h3>Table of Contents</h3>
  <ol>{"".join(f"<li>{s.section_name}</li>" for s in sections)}</ol>
</div>
{section_html}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/parse-rfp", response_model=ParseRFPResponse, summary="Parse and Analyse RFP")
async def parse_rfp(payload: ParseRFPRequest) -> ParseRFPResponse:
    """
    Parse a Request for Proposal (RFP) document and extract key information.

    Identifies requirements, evaluation criteria, deadlines, budget, and
    recommends proposal sections.
    """
    try:
        schema = (
            "title (str), issuer (str), deadline (str), budget_range (str), scope (str), "
            "requirements (list[str]), evaluation_criteria (list[str]), "
            "submission_instructions (str), "
            "key_dates (list of {event (str), date (str)}), "
            "recommended_sections (list[str])"
        )
        result = await ai_service.extract_structured(
            f"Parse this RFP document:\n\n{payload.rfp_text[:5000]}", schema
        )
        return ParseRFPResponse(
            title=result.get("title", "Untitled RFP"),
            issuer=result.get("issuer", "Unknown Issuer"),
            deadline=result.get("deadline", "Not specified"),
            budget_range=result.get("budget_range", "Not specified"),
            scope=result.get("scope", "Refer to full RFP document"),
            requirements=result.get("requirements", ["Detailed requirements not extracted"]),
            evaluation_criteria=result.get("evaluation_criteria", ["Quality", "Price", "Experience"]),
            submission_instructions=result.get("submission_instructions", "See full RFP document"),
            key_dates=result.get("key_dates", [{"event": "Submission Deadline", "date": "TBD"}]),
            recommended_sections=result.get(
                "recommended_sections",
                ["Executive Summary", "Technical Approach", "Team", "Pricing", "References"],
            ),
        )
    except Exception as exc:
        log.error("proposals.parse_rfp.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"RFP parsing failed: {exc}") from exc


@router.post("/generate-section", response_model=GenerateSectionResponse, summary="Generate Proposal Section")
async def generate_section(payload: GenerateSectionRequest) -> GenerateSectionResponse:
    """
    Generate content for a specific section of a proposal.

    Tailors the content to the RFP requirements and the company's capabilities.
    """
    try:
        content = await ai_service.generate_proposal_section(
            rfp_text=payload.rfp_text,
            section=payload.section_name,
            company_info=payload.company_info,
        )
        return GenerateSectionResponse(
            section_name=payload.section_name,
            content=content,
            word_count=len(content.split()),
        )
    except Exception as exc:
        log.error("proposals.generate_section.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Section generation failed: {exc}") from exc


@router.post("/full-proposal", response_model=FullProposalResponse, summary="Generate Full Proposal")
async def full_proposal(payload: FullProposalRequest) -> FullProposalResponse:
    """
    Generate a complete multi-section proposal in response to an RFP.

    Generates each requested section sequentially and assembles them into a
    cohesive document with HTML output.
    """
    try:
        company_str = (
            f"Company: {payload.company_info.name}. "
            f"{payload.company_info.description} "
            f"Key clients: {', '.join(payload.company_info.key_clients[:5])}. "
            f"Certifications: {', '.join(payload.company_info.certifications[:5])}."
        )
        if payload.custom_instructions:
            company_str += f" Additional instructions: {payload.custom_instructions}"

        generated_sections: list[ProposalSection] = []
        for section_name in payload.sections:
            content = await ai_service.generate_proposal_section(
                rfp_text=payload.rfp_text,
                section=section_name,
                company_info=company_str,
            )
            generated_sections.append(
                ProposalSection(
                    section_name=section_name,
                    content=content,
                    word_count=len(content.split()),
                )
            )

        total_words = sum(s.word_count for s in generated_sections)
        title = f"Proposal — {payload.company_info.name}"
        html = _build_html_proposal(title, payload.company_info.name, generated_sections)

        return FullProposalResponse(
            title=title,
            sections=generated_sections,
            total_word_count=total_words,
            html_proposal=html,
        )
    except Exception as exc:
        log.error("proposals.full_proposal.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Proposal generation failed: {exc}") from exc


@router.get("/templates", response_model=list[ProposalTemplate], summary="List Proposal Templates")
async def list_templates() -> list[ProposalTemplate]:
    """
    Return all available proposal templates.

    Templates provide pre-defined section structures for common proposal types.
    """
    return [ProposalTemplate(**t) for t in TEMPLATES]
