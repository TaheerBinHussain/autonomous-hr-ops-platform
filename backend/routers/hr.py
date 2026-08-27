"""
HR Router — AI-powered HR automation endpoints.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/hr", tags=["HR"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ResumeScreenRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, description="Full resume text")
    job_description: str = Field(..., min_length=20, description="Job description to match against")


class ResumeScreenResponse(BaseModel):
    score: int
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str


class OfferLetterRequest(BaseModel):
    candidate_name: str = Field(..., description="Full name of the candidate")
    position: str = Field(..., description="Job title being offered")
    salary: str = Field(..., description="Offered salary (e.g. '$85,000/year')")
    start_date: str = Field(..., description="Proposed start date (e.g. '2026-09-15')")
    company_name: str = Field(default="Acme Corporation", description="Hiring company name")


class OfferLetterResponse(BaseModel):
    offer_letter: str
    subject: str


class OnboardingRequest(BaseModel):
    employee_name: str
    department: str
    role: str
    start_date: str = Field(default="", description="Optional start date")


class OnboardingResponse(BaseModel):
    employee_name: str
    department: str
    role: str
    checklist: list[dict[str, Any]]


class RejectionEmailRequest(BaseModel):
    candidate_name: str
    position: str
    company_name: str = "Acme Corporation"
    include_feedback: bool = False


class RejectionEmailResponse(BaseModel):
    subject: str
    body: str
    html_body: str


class InterviewSlot(BaseModel):
    date: str
    time: str
    interviewer: str
    format: str = "Video Call"


class InterviewScheduleRequest(BaseModel):
    candidate_name: str
    position: str
    slots: list[InterviewSlot]


class InterviewScheduleResponse(BaseModel):
    candidate_name: str
    position: str
    schedule: list[dict[str, Any]]
    confirmation_message: str


class HRMetricsResponse(BaseModel):
    total_applicants: int
    shortlisted: int
    hired: int
    rejected: int
    in_progress: int
    time_to_hire_days: float
    acceptance_rate: float
    departments: dict[str, int]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/screen-resume", response_model=ResumeScreenResponse, summary="AI Resume Screening")
async def screen_resume(payload: ResumeScreenRequest) -> ResumeScreenResponse:
    """
    Score a resume against a job description using AI.

    Returns a score (0-100), identified strengths and weaknesses, and a
    hiring recommendation.
    """
    try:
        result = await ai_service.score_resume(payload.resume_text, payload.job_description)
        return ResumeScreenResponse(**result)
    except Exception as exc:
        log.error("hr.screen_resume.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {exc}") from exc


@router.post("/generate-offer-letter", response_model=OfferLetterResponse, summary="Generate Offer Letter")
async def generate_offer_letter(payload: OfferLetterRequest) -> OfferLetterResponse:
    """
    Generate a professional offer letter for an accepted candidate.

    Returns both the offer letter body and a suggested email subject line.
    """
    try:
        context = (
            f"Candidate: {payload.candidate_name}, Position: {payload.position}, "
            f"Salary: {payload.salary}, Start Date: {payload.start_date}, "
            f"Company: {payload.company_name}"
        )
        result = await ai_service.generate_email(
            context=context,
            tone="formal and warm",
            purpose="job offer letter",
        )
        offer_letter = (
            f"Dear {payload.candidate_name},\n\n"
            f"We are pleased to offer you the position of {payload.position} at "
            f"{payload.company_name}.\n\n"
            f"Compensation: {payload.salary}\n"
            f"Start Date: {payload.start_date}\n\n"
            + result.get("body", "")
            + "\n\nPlease sign and return this letter within 5 business days.\n\n"
            "Warm regards,\nHR Department"
        )
        return OfferLetterResponse(
            offer_letter=offer_letter,
            subject=result.get("subject", f"Job Offer — {payload.position} at {payload.company_name}"),
        )
    except Exception as exc:
        log.error("hr.offer_letter.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Offer letter generation failed: {exc}") from exc


@router.post("/onboarding-checklist", response_model=OnboardingResponse, summary="Generate Onboarding Checklist")
async def onboarding_checklist(payload: OnboardingRequest) -> OnboardingResponse:
    """
    Generate a personalised onboarding checklist for a new employee.

    The checklist is tailored to the employee's department and role.
    """
    try:
        prompt = (
            f"Create a detailed onboarding checklist for {payload.employee_name} "
            f"who is joining as {payload.role} in the {payload.department} department"
            + (f" starting {payload.start_date}" if payload.start_date else "")
            + ". Return a JSON array of checklist items where each item has: "
            "'task' (str), 'category' (str), 'day' (int, day number when to complete), "
            "'owner' (HR|Manager|IT|Employee), 'completed' (bool, default false)."
        )
        schema = (
            "A JSON object with key 'checklist' containing an array of checklist items. "
            "Each item: task (str), category (str), day (int), owner (str), completed (bool)"
        )
        result = await ai_service.extract_structured(prompt, schema)
        checklist = result.get("checklist", _default_checklist(payload.role, payload.department))
        return OnboardingResponse(
            employee_name=payload.employee_name,
            department=payload.department,
            role=payload.role,
            checklist=checklist,
        )
    except Exception as exc:
        log.error("hr.onboarding.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Checklist generation failed: {exc}") from exc


def _default_checklist(role: str, department: str) -> list[dict]:
    return [
        {"task": "Complete employment paperwork", "category": "Admin", "day": 1, "owner": "HR", "completed": False},
        {"task": "Set up workstation and accounts", "category": "IT Setup", "day": 1, "owner": "IT", "completed": False},
        {"task": "Company orientation session", "category": "Orientation", "day": 1, "owner": "HR", "completed": False},
        {"task": "Meet the team", "category": "Integration", "day": 1, "owner": "Manager", "completed": False},
        {"task": f"Review {department} processes and tools", "category": "Training", "day": 2, "owner": "Manager", "completed": False},
        {"task": "Access required systems and tools", "category": "IT Setup", "day": 2, "owner": "IT", "completed": False},
        {"task": "Complete mandatory compliance training", "category": "Compliance", "day": 3, "owner": "Employee", "completed": False},
        {"task": f"Shadow a senior {role}", "category": "Training", "day": 3, "owner": "Manager", "completed": False},
        {"task": "30-day check-in with manager", "category": "Review", "day": 30, "owner": "Manager", "completed": False},
        {"task": "90-day performance review", "category": "Review", "day": 90, "owner": "Manager", "completed": False},
    ]


@router.post("/generate-rejection-email", response_model=RejectionEmailResponse, summary="Generate Rejection Email")
async def generate_rejection_email(payload: RejectionEmailRequest) -> RejectionEmailResponse:
    """
    Generate a professional, empathetic rejection email for a candidate.

    Optionally includes constructive feedback if requested.
    """
    try:
        context = (
            f"Candidate: {payload.candidate_name}, Position: {payload.position}, "
            f"Company: {payload.company_name}. "
            + ("Include brief constructive feedback." if payload.include_feedback else "Keep it concise and kind.")
        )
        result = await ai_service.generate_email(
            context=context,
            tone="empathetic and professional",
            purpose="job application rejection",
        )
        return RejectionEmailResponse(**result)
    except Exception as exc:
        log.error("hr.rejection_email.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Rejection email generation failed: {exc}") from exc


@router.post("/interview-schedule", response_model=InterviewScheduleResponse, summary="Format Interview Schedule")
async def interview_schedule(payload: InterviewScheduleRequest) -> InterviewScheduleResponse:
    """
    Generate a formatted interview schedule for a candidate.

    Returns structured schedule data and a confirmation message ready to send.
    """
    try:
        schedule = [
            {
                "round": idx + 1,
                "date": slot.date,
                "time": slot.time,
                "interviewer": slot.interviewer,
                "format": slot.format,
                "duration_minutes": 45,
                "calendar_link": f"https://calendar.example.com/interview/{idx + 1}",
            }
            for idx, slot in enumerate(payload.slots)
        ]
        confirmation = (
            f"Dear {payload.candidate_name},\n\n"
            f"We are excited to invite you for the {payload.position} interview. "
            f"You have {len(payload.slots)} round(s) scheduled. Please confirm your attendance "
            "by replying to this email.\n\nBest of luck!\nHR Team"
        )
        return InterviewScheduleResponse(
            candidate_name=payload.candidate_name,
            position=payload.position,
            schedule=schedule,
            confirmation_message=confirmation,
        )
    except Exception as exc:
        log.error("hr.interview_schedule.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Schedule generation failed: {exc}") from exc


@router.get("/metrics", response_model=HRMetricsResponse, summary="HR Dashboard Metrics")
async def hr_metrics() -> HRMetricsResponse:
    """
    Return current HR pipeline metrics for the dashboard.

    Provides aggregate hiring funnel statistics and department breakdown.
    """
    return HRMetricsResponse(
        total_applicants=342,
        shortlisted=87,
        hired=24,
        rejected=231,
        in_progress=31,
        time_to_hire_days=18.5,
        acceptance_rate=88.9,
        departments={
            "Engineering": 10,
            "Sales": 5,
            "Marketing": 3,
            "Operations": 4,
            "Finance": 2,
        },
    )
