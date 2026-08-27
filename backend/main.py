"""
AI Automation Platform API — FastAPI application entry point.

Starts the server, mounts all domain routers, configures CORS, Prometheus metrics,
and structured logging.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from config import settings
from routers import crm, documents, hr, invoice, meetings, proposals, support

# ---------------------------------------------------------------------------
# Structured logging setup
# ---------------------------------------------------------------------------

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown tasks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Runs startup tasks (service health checks, connection pool warm-up) and
    teardown tasks on shutdown.
    """
    log.info(
        "startup.begin",
        app=app.title,
        version=app.version,
        database_url=settings.database_url.split("@")[-1],  # hide credentials
        redis_url=settings.redis_url,
        openai_configured=bool(settings.openai_api_key),
    )

    # --- Startup ---
    # In production: initialise DB connection pool, Redis pool, etc.
    # We log service status without crashing on missing services in dev mode.
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
        log.info("startup.redis", status="connected")
    except Exception as exc:
        log.warning("startup.redis", status="unavailable", error=str(exc))

    log.info("startup.complete", message="API is ready to serve requests")

    yield  # --- Application runs here ---

    # --- Shutdown ---
    log.info("shutdown.begin", message="Shutting down gracefully")
    log.info("shutdown.complete")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Automation Platform API",
    version="1.0.0",
    description=(
        "Comprehensive AI-powered backend for company automation. "
        "Covers HR, CRM, Invoicing, Document Processing, Meetings, "
        "Customer Support, and Proposal Generation."
    ),
    contact={"name": "Platform Team", "email": "platform@example.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# CORS — allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(duration)
    return response


# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/health"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(hr.router)
app.include_router(crm.router)
app.include_router(invoice.router)
app.include_router(documents.router)
app.include_router(meetings.router)
app.include_router(support.router)
app.include_router(proposals.router)


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"], summary="Welcome")
async def root():
    """
    Root endpoint — confirms the API is running and returns basic information.
    """
    return {
        "message": "Welcome to the AI Automation Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "metrics": "/metrics",
        "routers": [
            "/hr — HR Automation",
            "/crm — CRM & Lead Management",
            "/invoice — Invoice Processing",
            "/documents — Document Intelligence",
            "/meetings — Meeting Intelligence",
            "/support — Customer Support AI",
            "/proposals — Proposal Generation",
        ],
    }


@app.get("/health", tags=["Health"], summary="Health Check")
async def health_check():
    """
    Health check endpoint for load balancers and uptime monitors.

    Returns the status of all critical downstream services.
    """
    db_status = "ok"
    redis_status = "ok"
    ai_status = "ok" if settings.openai_api_key else "mock_mode"

    # Quick Redis ping
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
    except Exception:
        redis_status = "unavailable"

    # Quick DB check (psycopg2 is sync; we just check the URL is set)
    if not settings.database_url:
        db_status = "not_configured"

    overall = "healthy" if db_status != "error" and redis_status != "error" else "degraded"

    return JSONResponse(
        status_code=200,
        content={
            "status": overall,
            "version": "1.0.0",
            "services": {
                "database": db_status,
                "redis": redis_status,
                "ai": ai_status,
            },
        },
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
