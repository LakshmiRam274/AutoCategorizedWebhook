"""
FastAPI application exposing the ticket auto-categorization webhook.

Endpoints:
  GET  /            -> basic service info
  GET  /health      -> health check
  POST /classify    -> classify a single ticket and return it enriched with
                        category / subcategory / priority
"""

import time

from fastapi import FastAPI, HTTPException

from app.classifier import classify_ticket
from app.logger import log_prediction
from app.models import TicketIn, TicketOut

app = FastAPI(
    title="Ticket Auto-Categorization Webhook",
    description=(
        "Receives a service desk ticket as JSON, uses an LLM with few-shot "
        "examples to classify category / subcategory / priority, and "
        "returns the ticket enriched with that classification."
    ),
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "service": "ticket-auto-categorization-webhook",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/classify", response_model=TicketOut)
async def classify(ticket: TicketIn):
    """Classify an incoming ticket and return the enriched ticket JSON."""
    start = time.perf_counter()

    try:
        result = await classify_ticket(ticket)
    except Exception as exc:  # noqa: BLE001 - surface any LLM/provider error to the caller
        raise HTTPException(status_code=502, detail=f"Classification failed: {exc}") from exc

    latency = time.perf_counter() - start
    log_prediction(ticket, result, latency)

    return result
