"""
Lightweight prediction logging for monitoring.

Each classification request/response pair is appended as one JSON line to
`config.LOG_FILE` (JSON Lines format), which is easy to tail, grep, or load
into pandas for monitoring dashboards.
"""

import json
import time
from pathlib import Path

from app import config
from app.models import TicketIn, TicketOut


def log_prediction(ticket_in: TicketIn, ticket_out: TicketOut, latency_seconds: float) -> None:
    """Append a single prediction record to the JSONL log file."""

    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ticket_id": ticket_in.ticket_id,
        "input": ticket_in.model_dump(),
        "output": {
            "category": ticket_out.category,
            "subcategory": ticket_out.subcategory,
            "priority": ticket_out.priority,
            "confidence": ticket_out.confidence,
            "reasoning": ticket_out.reasoning,
        },
        "model_used": ticket_out.model_used,
        "latency_seconds": round(latency_seconds, 4),
    }

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
