"""
Pydantic models for the ticket auto-categorization webhook.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    """Incoming, raw service desk ticket."""

    ticket_id: str = Field(..., description="Unique identifier of the ticket")
    subject: str = Field(..., description="Short ticket subject / title")
    description: str = Field(..., description="Full ticket description / body")
    requester: Optional[str] = Field(
        default=None, description="Name or email of the person who raised the ticket"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Any extra fields the source system sends along"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ticket_id": "TCK-2001",
                    "subject": "Cannot connect to office VPN",
                    "description": (
                        "Since this morning I keep getting an authentication "
                        "error when trying to connect to the corporate VPN "
                        "from home. I have tried restarting my laptop twice."
                    ),
                    "requester": "asha.iyer@example.com",
                }
            ]
        }
    }


class TicketOut(TicketIn):
    """Ticket enriched with the LLM's classification."""

    category: str = Field(..., description="High-level ticket category")
    subcategory: str = Field(..., description="Specific sub-area within the category")
    priority: str = Field(..., description="One of Low, Medium, High, Critical")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model's self-reported confidence (0-1)"
    )
    reasoning: str = Field(..., description="Short explanation for the classification")
    model_used: str = Field(..., description="Identifier of the LLM model used")
