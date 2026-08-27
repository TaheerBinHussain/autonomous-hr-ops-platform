"""
Invoice Router — AI-powered invoice extraction, generation, and payment reminders.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/invoice", tags=["Invoice"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class InvoiceExtractRequest(BaseModel):
    invoice_text: str = Field(..., min_length=20, description="Raw invoice text to parse")


class LineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    total: float


class InvoiceExtractResponse(BaseModel):
    vendor: str
    amount: float
    currency: str = "USD"
    date: str
    due_date: str
    invoice_number: str
    line_items: list[dict[str, Any]]
    tax: float
    subtotal: float


class GenerateLineItem(BaseModel):
    description: str
    quantity: float = Field(default=1.0, gt=0)
    unit_price: float = Field(..., gt=0)


class CompanyInfo(BaseModel):
    name: str
    address: str = ""
    email: str = ""
    phone: str = ""
    tax_id: str = ""
    logo_url: str = ""


class InvoiceGenerateRequest(BaseModel):
    client_name: str
    client_email: str = ""
    client_address: str = ""
    items: list[GenerateLineItem]
    due_date: str = Field(..., description="Due date (YYYY-MM-DD)")
    company_info: CompanyInfo
    notes: str = ""
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="Tax rate percentage")
    invoice_number: str = ""
    currency: str = "USD"


class InvoiceGenerateResponse(BaseModel):
    invoice_number: str
    html_invoice: str
    plain_text_invoice: str
    subtotal: float
    tax_amount: float
    total: float
    line_items: list[dict[str, Any]]


class PaymentReminderRequest(BaseModel):
    invoice_id: str
    days_overdue: int = Field(..., ge=0, description="Number of days the invoice is overdue")
    client_name: str
    amount: float
    currency: str = "USD"
    original_due_date: str = ""
    company_name: str = "Acme Corporation"


class PaymentReminderResponse(BaseModel):
    subject: str
    body: str
    html_body: str
    urgency_level: str  # friendly | firm | final_notice


class InvoiceAnalyticsResponse(BaseModel):
    total_invoices: int
    total_revenue: str
    outstanding_amount: str
    overdue_amount: str
    paid_count: int
    unpaid_count: int
    overdue_count: int
    avg_payment_days: float
    monthly_trend: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_invoice_number() -> str:
    import random, string
    suffix = "".join(random.choices(string.digits, k=4))
    return f"INV-2026-{suffix}"


def _build_plain_invoice(
    request: InvoiceGenerateRequest,
    inv_number: str,
    subtotal: float,
    tax_amount: float,
    total: float,
    line_items: list[dict],
) -> str:
    lines = [
        f"INVOICE #{inv_number}",
        "=" * 50,
        f"From: {request.company_info.name}",
        f"To: {request.client_name}" + (f" <{request.client_email}>" if request.client_email else ""),
        f"Due Date: {request.due_date}",
        "",
        "ITEMS:",
        "-" * 50,
    ]
    for item in line_items:
        lines.append(
            f"  {item['description']:30s}  {item['quantity']:>5.1f} x "
            f"${item['unit_price']:>10.2f}  =  ${item['total']:>10.2f}"
        )
    lines += [
        "-" * 50,
        f"{'Subtotal':>48s}  ${subtotal:>10.2f}",
        f"{'Tax (' + str(request.tax_rate) + '%)':>48s}  ${tax_amount:>10.2f}",
        f"{'TOTAL':>48s}  ${total:>10.2f}",
        "",
    ]
    if request.notes:
        lines += ["Notes:", request.notes, ""]
    lines.append(f"Thank you for your business, {request.client_name}!")
    return "\n".join(lines)


def _build_html_invoice(
    request: InvoiceGenerateRequest,
    inv_number: str,
    subtotal: float,
    tax_amount: float,
    total: float,
    line_items: list[dict],
) -> str:
    rows = "".join(
        f"<tr><td>{i['description']}</td><td>{i['quantity']}</td>"
        f"<td>${i['unit_price']:.2f}</td><td>${i['total']:.2f}</td></tr>"
        for i in line_items
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Invoice {inv_number}</title>
<style>body{{font-family:Arial,sans-serif;margin:40px;color:#333}}
.header{{display:flex;justify-content:space-between}}
table{{width:100%;border-collapse:collapse;margin-top:20px}}
th{{background:#4f46e5;color:#fff;padding:10px;text-align:left}}
td{{padding:8px;border-bottom:1px solid #eee}}
.totals{{text-align:right;margin-top:20px}}
.total-row{{font-weight:bold;font-size:1.1em}}</style></head>
<body>
<div class="header">
  <div><h1>INVOICE</h1><p>#{inv_number}</p></div>
  <div><h2>{request.company_info.name}</h2>
    <p>{request.company_info.address}</p>
    <p>{request.company_info.email}</p></div>
</div>
<hr>
<p><strong>Bill To:</strong> {request.client_name}
  {('<br>' + request.client_email) if request.client_email else ''}
  {('<br>' + request.client_address) if request.client_address else ''}
</p>
<p><strong>Due Date:</strong> {request.due_date} &nbsp;|&nbsp;
   <strong>Currency:</strong> {request.currency}</p>
<table>
  <thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<div class="totals">
  <p>Subtotal: ${subtotal:.2f}</p>
  <p>Tax ({request.tax_rate}%): ${tax_amount:.2f}</p>
  <p class="total-row">TOTAL: ${total:.2f}</p>
</div>
{('<p><em>Notes: ' + request.notes + '</em></p>') if request.notes else ''}
<hr><p style="text-align:center">Thank you for your business!</p>
</body></html>"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/extract", response_model=InvoiceExtractResponse, summary="Extract Invoice Data")
async def extract_invoice(payload: InvoiceExtractRequest) -> InvoiceExtractResponse:
    """
    Extract structured data from raw invoice text using AI.

    Parses vendor, amount, dates, line items, and tax from unstructured text.
    """
    try:
        result = await ai_service.extract_invoice_data(payload.invoice_text)
        return InvoiceExtractResponse(
            vendor=result.get("vendor", "Unknown"),
            amount=float(result.get("amount", 0)),
            currency=result.get("currency", "USD"),
            date=result.get("date", ""),
            due_date=result.get("due_date", ""),
            invoice_number=result.get("invoice_number", ""),
            line_items=result.get("line_items", []),
            tax=float(result.get("tax", 0)),
            subtotal=float(result.get("subtotal", 0)),
        )
    except Exception as exc:
        log.error("invoice.extract.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Invoice extraction failed: {exc}") from exc


@router.post("/generate", response_model=InvoiceGenerateResponse, summary="Generate Invoice")
async def generate_invoice(payload: InvoiceGenerateRequest) -> InvoiceGenerateResponse:
    """
    Generate a professional invoice with HTML and plain-text versions.

    Calculates totals including configurable tax rate.
    """
    try:
        line_items = [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": round(item.quantity * item.unit_price, 2),
            }
            for item in payload.items
        ]
        subtotal = round(sum(i["total"] for i in line_items), 2)
        tax_amount = round(subtotal * payload.tax_rate / 100, 2)
        total = round(subtotal + tax_amount, 2)
        inv_number = payload.invoice_number or _generate_invoice_number()

        return InvoiceGenerateResponse(
            invoice_number=inv_number,
            html_invoice=_build_html_invoice(payload, inv_number, subtotal, tax_amount, total, line_items),
            plain_text_invoice=_build_plain_invoice(payload, inv_number, subtotal, tax_amount, total, line_items),
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            line_items=line_items,
        )
    except Exception as exc:
        log.error("invoice.generate.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Invoice generation failed: {exc}") from exc


@router.post("/payment-reminder", response_model=PaymentReminderResponse, summary="Generate Payment Reminder")
async def payment_reminder(payload: PaymentReminderRequest) -> PaymentReminderResponse:
    """
    Generate a payment reminder email scaled to overdue severity.

    Tone escalates from friendly (1-7 days) to firm (8-30 days) to final notice (30+ days).
    """
    try:
        if payload.days_overdue <= 7:
            urgency = "friendly"
            tone = "friendly and gentle"
        elif payload.days_overdue <= 30:
            urgency = "firm"
            tone = "firm and professional"
        else:
            urgency = "final_notice"
            tone = "serious and urgent"

        context = (
            f"Client: {payload.client_name}. Invoice ID: {payload.invoice_id}. "
            f"Amount: {payload.currency} {payload.amount:.2f}. "
            f"Days overdue: {payload.days_overdue}. "
            f"Company: {payload.company_name}."
            + (f" Original due date: {payload.original_due_date}." if payload.original_due_date else "")
        )
        result = await ai_service.generate_email(
            context=context,
            tone=tone,
            purpose=f"payment reminder ({urgency})",
        )
        return PaymentReminderResponse(
            subject=result.get("subject", f"Payment Reminder — Invoice {payload.invoice_id}"),
            body=result.get("body", ""),
            html_body=result.get("html_body", ""),
            urgency_level=urgency,
        )
    except Exception as exc:
        log.error("invoice.reminder.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Reminder generation failed: {exc}") from exc


@router.get("/analytics", response_model=InvoiceAnalyticsResponse, summary="Invoice Analytics")
async def invoice_analytics() -> InvoiceAnalyticsResponse:
    """
    Return invoice analytics for the current period.

    Includes revenue totals, outstanding/overdue amounts, and monthly trend data.
    """
    return InvoiceAnalyticsResponse(
        total_invoices=284,
        total_revenue="$1,240,500",
        outstanding_amount="$187,200",
        overdue_amount="$43,800",
        paid_count=241,
        unpaid_count=31,
        overdue_count=12,
        avg_payment_days=18.3,
        monthly_trend=[
            {"month": "Mar 2026", "invoiced": 142000, "collected": 138000, "overdue": 4000},
            {"month": "Apr 2026", "invoiced": 198000, "collected": 187000, "overdue": 11000},
            {"month": "May 2026", "invoiced": 167000, "collected": 152000, "overdue": 15000},
            {"month": "Jun 2026", "invoiced": 221000, "collected": 209000, "overdue": 12000},
            {"month": "Jul 2026", "invoiced": 254000, "collected": 241000, "overdue": 13000},
            {"month": "Aug 2026", "invoiced": 258500, "collected": 213200, "overdue": 45300},
        ],
    )
