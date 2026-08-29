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


# ---------------------------------------------------------------------------
# Live Demo End-to-End Pipeline Endpoint
# ---------------------------------------------------------------------------

class CandidatePipelineRequest(BaseModel):
    job_title: str = Field(default="Senior AI Platform Engineer", description="Job title")
    job_description: str = Field(default="Requires Python, FastAPI, Docker, Kubernetes, n8n automation, OpenAI LLM integration", description="Job requirements")
    candidate_name: str = Field(default="Sarah Connor", description="Candidate name")
    candidate_email: str = Field(default="sarah.connor@example.com", description="Candidate email")
    salary_offered: str = Field(default="$125,000 / year", description="Offered salary if selected")
    score_threshold: int = Field(default=70, ge=0, le=100, description="Minimum score to pass screening")
    resume_text: str = Field(..., min_length=30, description="Candidate resume text")


class CandidatePipelineResponse(BaseModel):
    status: str
    passed: bool
    candidate_name: str
    candidate_email: str
    job_title: str
    score: int
    score_threshold: int
    recommendation: str
    strengths: list[str]
    weaknesses: list[str]
    email_action: str
    email_subject: str
    email_body: str
    email_html: str
    interview_slots: list[str] = Field(default_factory=list)
    meet_link: str = Field(default="")
    onboarding_checklist: list[str] = Field(default_factory=list)
    n8n_event: dict[str, Any]


@router.post("/process-candidate-pipeline", response_model=CandidatePipelineResponse, summary="End-to-End AI HR Recruitment Pipeline (Live Demo)")
async def process_candidate_pipeline(payload: CandidatePipelineRequest) -> CandidatePipelineResponse:
    """
    Complete Autonomous HR Pipeline for Live Supervisor Demo:
    1. HR Posts Job Requirements
    2. Candidate Applies & Submits Resume
    3. AI Screens and Scores Resume (0-100)
    4. If Score >= Threshold: Autonomous Offer Letter & Selection Email is drafted and dispatched!
    5. If Score < Threshold: Autonomous Constructive Rejection Email is drafted and dispatched!
    """
    try:
        # Step 1: Score Resume against Job Description
        screen_result = await ai_service.score_resume(payload.resume_text, payload.job_description)
        score = int(screen_result.get("score", 50))
        strengths = screen_result.get("strengths", ["Relevant experience"])
        weaknesses = screen_result.get("weaknesses", ["Needs more domain context"])
        recommendation = screen_result.get("recommendation", "Proceed with interview")

        passed = score >= payload.score_threshold

        # Step 2: Autonomous Decision & Email Generation
        if passed:
            email_action = "OFFER_LETTER_SENT"
            context = (
                f"Candidate: {payload.candidate_name}, Email: {payload.candidate_email}, "
                f"Position: {payload.job_title}, Salary: {payload.salary_offered}, "
                f"Screening Score: {score}/100. Key Strengths: {', '.join(strengths)}."
            )
            email_res = await ai_service.generate_email(
                context=context,
                tone="enthusiastic, professional and official",
                purpose="job offer and selection notification",
            )
            subject = email_res.get("subject", f"🎉 Job Offer: {payload.job_title} at TechCorp AI")
            body = (
                f"Dear {payload.candidate_name},\n\n"
                f"Congratulations! Based on your outstanding resume screening score of {score}/100, "
                f"we are thrilled to offer you the position of {payload.job_title}.\n\n"
                f"📋 Position: {payload.job_title}\n"
                f"💰 Compensation: {payload.salary_offered}\n"
                f"🌟 Outstanding Strengths Identified: {', '.join(strengths[:3])}\n\n"
                + email_res.get("body", "") + "\n\n"
                "Please confirm acceptance within 3 business days.\n\n"
                "Best Regards,\nAutonomous HR AI System & Hiring Committee"
            )
        else:
            email_action = "REJECTION_FEEDBACK_SENT"
            context = (
                f"Candidate: {payload.candidate_name}, Position: {payload.position if hasattr(payload, 'position') else payload.job_title}. "
                f"Score: {score}/100. Areas for growth: {', '.join(weaknesses)}."
            )
            email_res = await ai_service.generate_email(
                context=context,
                tone="kind, encouraging and professional",
                purpose="candidate application status feedback",
            )
            subject = email_res.get("subject", f"Application Status: {payload.job_title}")
            body = (
                f"Dear {payload.candidate_name},\n\n"
                f"Thank you for applying for the {payload.job_title} role.\n\n"
                f"After evaluating your application with our AI Screening System (Score: {score}/100 vs Threshold: {payload.score_threshold}/100), "
                f"we have decided to proceed with other candidates whose experience aligns more closely with our current technical requirements.\n\n"
                f"💡 Areas of Feedback: {', '.join(weaknesses[:3])}\n\n"
                + email_res.get("body", "") + "\n\n"
                "We wish you the best in your professional journey.\n\n"
                "Warm regards,\nHR Team"
            )

        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; background: #0f172a; color: #f8fafc; border-radius: 10px;">
            <h2 style="color: {'#10b981' if passed else '#ef4444'};">{'🎉 Application Successful!' if passed else 'Application Status Update'}</h2>
            <p><strong>Candidate:</strong> {payload.candidate_name} ({payload.candidate_email})</p>
            <p><strong>Role:</strong> {payload.job_title}</p>
            <p><strong>AI Screening Score:</strong> <span style="font-size: 18px; font-weight: bold; color: {'#10b981' if passed else '#ef4444'};">{score}/100</span> (Threshold: {payload.score_threshold}/100)</p>
            <hr style="border-color: #334155;" />
            <pre style="white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.6;">{body}</pre>
        </div>
        """

        n8n_event = {
            "event": "candidate_screened",
            "candidate": payload.candidate_name,
            "email": payload.candidate_email,
            "job": payload.job_title,
            "score": score,
            "passed": passed,
            "action": email_action,
            "timestamp": date.today().isoformat(),
        }

        interview_slots = []
        meet_link = ""
        onboarding_checklist = []

        if passed:
            cand_slug = payload.candidate_name.lower().replace(" ", "-")
            meet_link = f"https://meet.jit.si/nexus-interview-{cand_slug}"
            interview_slots = [
                "Tomorrow at 10:00 AM EST (Technical Panel Deep-Dive)",
                "Tomorrow at 02:00 PM EST (Architecture & Systems Review)",
                "Day after tomorrow at 11:00 AM EST (VP Engineering Sync)"
            ]
            onboarding_checklist = [
                "Issue Company Laptop & Hardware Security Key",
                "Provision GitHub Enterprise & AWS IAM Developer Access",
                "Invite to Slack Channels (#welcome, #engineering, #ai-platform)",
                "Schedule Day-1 Orientation with HR Manager",
                "Sign NDA & Employment Agreement Package"
            ]

        # Dispatch real email to Mailpit SMTP
        try:
            from services.email_service import email_service
            email_service.send_email(
                to_email=payload.candidate_email,
                subject=subject,
                html_body=html_body,
                text_body=body,
            )
        except Exception as smtp_err:
            log.warning("hr.candidate_pipeline.smtp_error", error=str(smtp_err))

        log.info("hr.candidate_pipeline.complete", candidate=payload.candidate_name, score=score, passed=passed)

        return CandidatePipelineResponse(
            status="SUCCESS",
            passed=passed,
            candidate_name=payload.candidate_name,
            candidate_email=payload.candidate_email,
            job_title=payload.job_title,
            score=score,
            score_threshold=payload.score_threshold,
            recommendation=recommendation,
            strengths=strengths,
            weaknesses=weaknesses,
            email_action=email_action,
            email_subject=subject,
            email_body=body,
            email_html=html_body,
            interview_slots=interview_slots,
            meet_link=meet_link,
            onboarding_checklist=onboarding_checklist,
            n8n_event=n8n_event,
        )
    except Exception as exc:
        log.error("hr.candidate_pipeline.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {exc}") from exc

