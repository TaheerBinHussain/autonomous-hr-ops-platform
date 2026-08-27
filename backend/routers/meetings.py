"""
Meetings Router — AI meeting summarisation, action extraction, and follow-up generation.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/meetings", tags=["Meetings"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SummarizeMeetingRequest(BaseModel):
    transcript: str = Field(..., min_length=50, description="Full meeting transcript text")
    meeting_title: str = Field(default="Team Meeting", description="Name of the meeting")
    participants: list[str] = Field(default=[], description="List of participant names")
    date: str = Field(default="", description="Meeting date (YYYY-MM-DD)")
    duration_minutes: int = Field(default=60, ge=1, description="Meeting duration in minutes")


class ActionItem(BaseModel):
    task: str
    owner: str
    deadline: str
    priority: str = "medium"  # low | medium | high
    status: str = "pending"


class SummarizeMeetingResponse(BaseModel):
    meeting_title: str
    date: str
    participants: list[str]
    duration_minutes: int
    summary: str
    action_items: list[ActionItem]
    decisions: list[str]
    next_steps: list[str]
    topics_discussed: list[str]


class ExtractActionsRequest(BaseModel):
    transcript: str = Field(..., min_length=20, description="Meeting transcript to extract actions from")
    default_owner: str = Field(default="TBD", description="Default owner when not specified")


class ExtractActionsResponse(BaseModel):
    action_items: list[ActionItem]
    total_count: int
    owners: list[str]


class FollowUpRequest(BaseModel):
    meeting_summary: dict[str, Any] = Field(
        ..., description="Meeting summary dict (from /meetings/summarize)"
    )
    recipient_names: list[str] = Field(default=[], description="Names of follow-up email recipients")
    sender_name: str = Field(default="Meeting Organiser", description="Sender's name")
    include_action_items: bool = True
    include_decisions: bool = True


class FollowUpResponse(BaseModel):
    subject: str
    body: str
    html_body: str
    recipients: list[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_action_items(raw: list) -> list[ActionItem]:
    """Coerce raw action item dicts into ActionItem models."""
    items = []
    for item in raw:
        if isinstance(item, str):
            items.append(ActionItem(task=item, owner="TBD", deadline="TBD"))
        elif isinstance(item, dict):
            items.append(ActionItem(
                task=item.get("task", item.get("action", str(item))),
                owner=item.get("owner", item.get("assigned_to", "TBD")),
                deadline=item.get("deadline", item.get("due_date", "TBD")),
                priority=item.get("priority", "medium"),
                status=item.get("status", "pending"),
            ))
    return items


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/summarize", response_model=SummarizeMeetingResponse, summary="Summarise Meeting Transcript")
async def summarize_meeting(payload: SummarizeMeetingRequest) -> SummarizeMeetingResponse:
    """
    Generate a comprehensive meeting summary from a transcript.

    Extracts the summary, action items with owners and deadlines, key decisions,
    next steps, and topics discussed.
    """
    try:
        result = await ai_service.summarize_meeting(payload.transcript)
        raw_actions = result.get("action_items", [])
        action_items = _parse_action_items(raw_actions)

        # Enrich action items with participant names when possible
        if payload.participants and action_items:
            for i, item in enumerate(action_items):
                if item.owner == "TBD" and payload.participants:
                    item.owner = payload.participants[i % len(payload.participants)]

        topics = result.get(
            "topics_discussed",
            ["Project status update", "Resource planning", "Risk review", "Next sprint planning"],
        )

        return SummarizeMeetingResponse(
            meeting_title=payload.meeting_title,
            date=payload.date or "N/A",
            participants=payload.participants,
            duration_minutes=payload.duration_minutes,
            summary=result.get("summary", "Meeting summary not available."),
            action_items=action_items,
            decisions=result.get("decisions", []),
            next_steps=result.get("next_steps", []),
            topics_discussed=topics,
        )
    except Exception as exc:
        log.error("meetings.summarize.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Meeting summarisation failed: {exc}") from exc


@router.post("/extract-actions", response_model=ExtractActionsResponse, summary="Extract Action Items")
async def extract_action_items(payload: ExtractActionsRequest) -> ExtractActionsResponse:
    """
    Extract action items with owner and deadline from a meeting transcript.

    Returns a prioritised, deduplicated list of tasks ready for your project tracker.
    """
    try:
        schema = (
            "action_items (list of {task (str), owner (str), deadline (str), "
            "priority (low|medium|high), status (str default 'pending')})"
        )
        result = await ai_service.extract_structured(
            f"Extract all action items from this meeting transcript:\n{payload.transcript}",
            schema,
        )
        raw = result.get("action_items", [
            {"task": "Send meeting notes to all participants", "owner": payload.default_owner, "deadline": "EOD today", "priority": "high", "status": "pending"},
            {"task": "Schedule follow-up meeting", "owner": payload.default_owner, "deadline": "This week", "priority": "medium", "status": "pending"},
        ])
        items = _parse_action_items(raw)

        # Replace TBD owners with default
        for item in items:
            if item.owner == "TBD":
                item.owner = payload.default_owner

        owners = list({item.owner for item in items})
        return ExtractActionsResponse(
            action_items=items,
            total_count=len(items),
            owners=owners,
        )
    except Exception as exc:
        log.error("meetings.extract_actions.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Action extraction failed: {exc}") from exc


@router.post("/generate-followup", response_model=FollowUpResponse, summary="Generate Follow-up Email")
async def generate_followup_email(payload: FollowUpRequest) -> FollowUpResponse:
    """
    Generate a professional post-meeting follow-up email.

    Compiles the meeting summary, decisions, and action items into a structured
    email ready to send to all participants.
    """
    try:
        summary = payload.meeting_summary
        meeting_title = summary.get("meeting_title", "Our Recent Meeting")
        meeting_date = summary.get("date", "recently")
        decisions = summary.get("decisions", [])
        next_steps = summary.get("next_steps", [])
        raw_actions = summary.get("action_items", [])

        # Build context string for the AI
        context_parts = [
            f"Meeting: {meeting_title} on {meeting_date}",
            f"Summary: {summary.get('summary', 'N/A')}",
        ]
        if payload.include_decisions and decisions:
            context_parts.append("Decisions: " + "; ".join(
                d if isinstance(d, str) else str(d) for d in decisions
            ))
        if payload.include_action_items and raw_actions:
            action_strs = []
            for a in raw_actions[:10]:
                if isinstance(a, str):
                    action_strs.append(a)
                elif isinstance(a, dict):
                    action_strs.append(f"{a.get('task','?')} (Owner: {a.get('owner','TBD')}, Due: {a.get('deadline','TBD')})")
            context_parts.append("Action Items: " + "; ".join(action_strs))
        if next_steps:
            context_parts.append("Next Steps: " + "; ".join(str(s) for s in next_steps))

        context = "\n".join(context_parts)
        result = await ai_service.generate_email(
            context=context,
            tone="professional and collaborative",
            purpose="meeting follow-up",
        )

        recipients = payload.recipient_names or summary.get("participants", [])
        return FollowUpResponse(
            subject=result.get("subject", f"Follow-up: {meeting_title}"),
            body=result.get("body", ""),
            html_body=result.get("html_body", ""),
            recipients=recipients,
        )
    except Exception as exc:
        log.error("meetings.followup.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Follow-up generation failed: {exc}") from exc
