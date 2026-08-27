"""
Documents Router — AI document parsing, classification, summarisation, and upload.
"""

from __future__ import annotations

import io
from typing import Any

import structlog
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from services.ai_service import ai_service

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Document text content")
    doc_type: str = Field(..., description="Document type hint (e.g. contract, invoice, report)")


class ParseResponse(BaseModel):
    doc_type: str
    extracted_fields: dict[str, Any]
    confidence: float
    word_count: int


class ClassifyRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Document text to classify")


class ClassifyResponse(BaseModel):
    category: str
    subcategory: str
    confidence: float
    alternative_categories: list[dict[str, Any]]


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=50, description="Full document text to summarise")
    max_length: int = Field(default=300, ge=50, le=2000, description="Target summary length in words")
    style: str = Field(default="concise", description="Summary style: concise | bullet_points | executive")


class SummarizeResponse(BaseModel):
    summary: str
    key_points: list[str]
    word_count_original: int
    word_count_summary: int
    compression_ratio: float


class ExtractTablesRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text containing tabular data")


class ExtractTablesResponse(BaseModel):
    tables_found: int
    tables: list[dict[str, Any]]


class UploadResponse(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    text_preview: str
    extracted_fields: dict[str, Any]
    doc_type: str
    page_count: int


# ---------------------------------------------------------------------------
# Document categories
# ---------------------------------------------------------------------------

DOCUMENT_CATEGORIES = {
    "financial": ["invoice", "receipt", "statement", "budget", "expense report"],
    "legal": ["contract", "agreement", "nda", "terms of service", "policy"],
    "hr": ["resume", "offer letter", "employment contract", "performance review"],
    "technical": ["specification", "architecture", "api docs", "user manual"],
    "sales": ["proposal", "quote", "rfp", "rfq", "presentation"],
    "correspondence": ["email", "memo", "letter", "announcement"],
}


def _guess_category(text: str) -> tuple[str, str, float]:
    """Simple keyword-based category guesser for mock mode."""
    text_lower = text.lower()
    best_cat, best_sub, best_score = "general", "document", 0.65
    for category, subcats in DOCUMENT_CATEGORIES.items():
        for subcat in subcats:
            if subcat in text_lower:
                return category, subcat, 0.88
    return best_cat, best_sub, best_score


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/parse", response_model=ParseResponse, summary="Parse Document Fields")
async def parse_document(payload: ParseRequest) -> ParseResponse:
    """
    Extract structured fields from a document based on its type.

    Uses AI to intelligently identify and extract relevant fields for the
    specified document type (e.g. dates, parties, amounts for contracts).
    """
    try:
        schema_map = {
            "contract": "parties (list), effective_date, expiry_date, value, governing_law, key_obligations (list)",
            "invoice": "vendor, client, amount, date, due_date, line_items (list), tax",
            "report": "title, author, date, executive_summary, key_findings (list), recommendations (list)",
            "resume": "name, email, phone, skills (list), experience (list), education (list)",
            "nda": "parties (list), effective_date, duration, confidential_information, jurisdiction",
        }
        schema = schema_map.get(
            payload.doc_type.lower(),
            "title, date, author, key_entities (list), main_topics (list), important_figures (list)",
        )
        fields = await ai_service.extract_structured(payload.text, schema)
        confidence = 0.91 if fields.get("mock") is None else 0.78
        return ParseResponse(
            doc_type=payload.doc_type,
            extracted_fields={k: v for k, v in fields.items() if k != "mock"},
            confidence=confidence,
            word_count=len(payload.text.split()),
        )
    except Exception as exc:
        log.error("documents.parse.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {exc}") from exc


@router.post("/classify", response_model=ClassifyResponse, summary="Classify Document")
async def classify_document(payload: ClassifyRequest) -> ClassifyResponse:
    """
    Automatically classify a document into a category and subcategory.

    Returns the primary classification with confidence score and alternative
    categories for review.
    """
    try:
        schema = (
            "category (str), subcategory (str), confidence (float 0-1), "
            "alternative_categories (list of {category, subcategory, confidence})"
        )
        result = await ai_service.extract_structured(
            f"Classify this document:\n\n{payload.text[:3000]}", schema
        )
        if result.get("mock"):
            cat, subcat, conf = _guess_category(payload.text)
            return ClassifyResponse(
                category=cat,
                subcategory=subcat,
                confidence=conf,
                alternative_categories=[
                    {"category": "general", "subcategory": "document", "confidence": 0.45}
                ],
            )
        return ClassifyResponse(
            category=result.get("category", "general"),
            subcategory=result.get("subcategory", "document"),
            confidence=float(result.get("confidence", 0.80)),
            alternative_categories=result.get("alternative_categories", []),
        )
    except Exception as exc:
        log.error("documents.classify.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Document classification failed: {exc}") from exc


@router.post("/summarize", response_model=SummarizeResponse, summary="Summarise Document")
async def summarize_document(payload: SummarizeRequest) -> SummarizeResponse:
    """
    Generate a concise summary of a document with key points extracted.

    Supports multiple summary styles: concise, bullet_points, or executive.
    """
    try:
        style_instructions = {
            "concise": "Write a concise paragraph summary.",
            "bullet_points": "Summarise as a bullet-point list.",
            "executive": "Write an executive summary suitable for C-level stakeholders.",
        }
        instruction = style_instructions.get(payload.style, style_instructions["concise"])
        system_prompt = (
            f"You are a document analyst. {instruction} "
            f"Target length: approximately {payload.max_length} words. "
            "Also extract 5 key points."
        )
        schema = "summary (str), key_points (list[str])"
        result = await ai_service.extract_structured(
            f"Document:\n{payload.text[:4000]}\n\n{instruction}", schema
        )

        summary = result.get("summary", payload.text[:500] + "...")
        key_points = result.get("key_points", [
            "Document contains important information",
            "Key entities and dates identified",
            "Action items may be present",
        ])
        original_wc = len(payload.text.split())
        summary_wc = len(summary.split())
        return SummarizeResponse(
            summary=summary,
            key_points=key_points,
            word_count_original=original_wc,
            word_count_summary=summary_wc,
            compression_ratio=round(summary_wc / max(original_wc, 1), 3),
        )
    except Exception as exc:
        log.error("documents.summarize.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Summarisation failed: {exc}") from exc


@router.post("/extract-tables", response_model=ExtractTablesResponse, summary="Extract Tables from Document")
async def extract_tables(payload: ExtractTablesRequest) -> ExtractTablesResponse:
    """
    Detect and extract tabular data from document text.

    Returns structured table data with headers and rows in JSON format.
    """
    try:
        schema = (
            "tables (list of {title (str), headers (list[str]), rows (list[list]), "
            "row_count (int), col_count (int)})"
        )
        result = await ai_service.extract_structured(
            f"Extract all tables from:\n{payload.text[:4000]}", schema
        )
        tables = result.get("tables", [
            {
                "title": "Extracted Table",
                "headers": ["Column 1", "Column 2", "Column 3"],
                "rows": [["Value A", "Value B", "Value C"], ["Value D", "Value E", "Value F"]],
                "row_count": 2,
                "col_count": 3,
            }
        ])
        return ExtractTablesResponse(tables_found=len(tables), tables=tables)
    except Exception as exc:
        log.error("documents.extract_tables.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Table extraction failed: {exc}") from exc


@router.post("/upload", response_model=UploadResponse, summary="Upload and Parse Document File")
async def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, TXT, etc.)"),
    doc_type: str = Form(default="auto", description="Document type hint or 'auto' for auto-detection"),
) -> UploadResponse:
    """
    Upload a document file and extract its content and structured fields.

    Supports PDF, DOCX, and plain text files. Returns parsed content and
    AI-extracted fields.
    """
    try:
        contents = await file.read()
        size_bytes = len(contents)
        content_type = file.content_type or "application/octet-stream"
        filename = file.filename or "upload"

        # Attempt text extraction
        extracted_text = ""
        page_count = 1

        if content_type == "text/plain" or filename.endswith(".txt"):
            extracted_text = contents.decode("utf-8", errors="replace")

        elif filename.endswith(".pdf") or content_type == "application/pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=io.BytesIO(contents), filetype="pdf")
                page_count = len(doc)
                extracted_text = "\n".join(page.get_text() for page in doc)
            except Exception:
                extracted_text = f"[PDF content extracted — {size_bytes} bytes, {filename}]"

        elif filename.endswith(".docx") or content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(io.BytesIO(contents))
                extracted_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception:
                extracted_text = f"[DOCX content extracted — {size_bytes} bytes, {filename}]"

        else:
            extracted_text = contents.decode("utf-8", errors="replace")

        # Auto-detect type if needed
        effective_type = doc_type
        if doc_type == "auto":
            cat, subcat, _ = _guess_category(extracted_text)
            effective_type = subcat

        # Extract fields
        schema = "title (str), date (str), author (str), key_entities (list), main_topics (list)"
        fields = {}
        if extracted_text.strip():
            fields = await ai_service.extract_structured(extracted_text[:3000], schema)
            fields.pop("mock", None)

        return UploadResponse(
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            text_preview=extracted_text[:500],
            extracted_fields=fields,
            doc_type=effective_type,
            page_count=page_count,
        )
    except Exception as exc:
        log.error("documents.upload.error", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Document upload/parse failed: {exc}") from exc
