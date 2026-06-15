"""
LLM-based ticket classifier.

This module is split into:
  - pure helper functions (load_samples, build_messages, extract_json,
    normalize_result) which have NO external dependencies and can be
    unit-tested without a network connection or any API key.
  - `classify_ticket`, the async function that actually calls the
    configured OpenAI-compatible LLM endpoint via httpx.

Few-shot examples are loaded from `data/samples.json` (see config.SAMPLES_FILE)
and injected into the prompt so the model has concrete examples of the
category / subcategory / priority taxonomy to follow.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import httpx

from app import config
from app.models import TicketIn, TicketOut


SYSTEM_PROMPT = """You are an expert IT Service Desk ticket triage assistant.

Given a ticket's subject and description, classify it into:
- "category": a high-level area, e.g. Hardware, Software, Network, Account & Access, Printing, Infrastructure
- "subcategory": a specific sub-area within that category
- "priority": exactly one of "Low", "Medium", "High", "Critical"
- "confidence": your confidence in this classification, a number between 0 and 1
- "reasoning": a short (one or two sentence) explanation for the classification

Use the example tickets provided as a guide for naming conventions and for how
priority should be judged (business impact + urgency).

Respond with ONLY a single valid JSON object and nothing else (no markdown
fences, no extra commentary), matching exactly this schema:
{"category": "...", "subcategory": "...", "priority": "Low|Medium|High|Critical", "confidence": 0.0, "reasoning": "..."}
"""


def load_samples(samples_file: str | None = None) -> List[Dict[str, Any]]:
    """Load few-shot example tickets from a JSON file.

    Returns an empty list (rather than raising) if the file is missing or
    malformed, so the service degrades gracefully without few-shot examples
    instead of crashing.
    """
    path = Path(samples_file or config.SAMPLES_FILE)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def build_messages(ticket: TicketIn, samples: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build the chat-completions `messages` array, embedding few-shot examples."""

    examples_blocks = []
    for ex in samples:
        classification = {
            "category": ex.get("category"),
            "subcategory": ex.get("subcategory"),
            "priority": ex.get("priority"),
        }
        examples_blocks.append(
            "Ticket:\n"
            f"Subject: {ex.get('subject', '')}\n"
            f"Description: {ex.get('description', '')}\n"
            f"Classification: {json.dumps(classification)}"
        )

    examples_text = "\n\n".join(examples_blocks)

    user_parts = []
    if examples_text:
        user_parts.append("Here are some previously classified example tickets:\n\n" + examples_text)

    user_parts.append(
        "Now classify the following NEW ticket. Respond with the JSON object only.\n\n"
        f"Ticket:\nSubject: {ticket.subject}\nDescription: {ticket.description}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(user_parts)},
    ]


def extract_json(text: str) -> Dict[str, Any]:
    """Extract a JSON object from an LLM text response.

    Handles the common cases of: a clean JSON object, a JSON object wrapped
    in ```json ... ``` markdown fences, or a JSON object surrounded by other
    text/commentary.
    """
    text = text.strip()

    # Strip surrounding markdown code fences, if present.
    fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to grabbing the first {...} block in the text.
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        return json.loads(brace_match.group(0))

    raise ValueError(f"Could not extract JSON from model response: {text!r}")


def normalize_result(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Fill in safe defaults and coerce types for a parsed classification dict."""

    category = str(parsed.get("category") or config.DEFAULT_CATEGORY).strip()
    subcategory = str(parsed.get("subcategory") or config.DEFAULT_SUBCATEGORY).strip()

    priority = str(parsed.get("priority") or config.DEFAULT_PRIORITY).strip().title()
    if priority not in config.VALID_PRIORITIES:
        priority = config.DEFAULT_PRIORITY

    try:
        confidence = float(parsed.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    reasoning = str(parsed.get("reasoning") or "").strip()

    return {
        "category": category,
        "subcategory": subcategory,
        "priority": priority,
        "confidence": confidence,
        "reasoning": reasoning,
    }


async def _call_llm(messages: List[Dict[str, str]]) -> str:
    """Call the configured OpenAI-compatible chat completions endpoint.

    Returns the raw text content of the model's reply.
    """
    headers = {"Content-Type": "application/json"}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"

    base_payload = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": 0.1,
    }

    url = f"{config.LLM_BASE_URL}/chat/completions"

    async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT) as client:
        if config.LLM_JSON_MODE:
            try:
                payload = {**base_payload, "response_format": {"type": "json_object"}}
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError:
                # Some providers / models reject response_format -> retry without it.
                pass

        resp = await client.post(url, headers=headers, json=base_payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def classify_ticket(ticket: TicketIn) -> TicketOut:
    """Classify a ticket and return it enriched with category/subcategory/priority."""

    samples = load_samples()
    messages = build_messages(ticket, samples)

    raw_content = await _call_llm(messages)
    parsed = extract_json(raw_content)
    normalized = normalize_result(parsed)

    return TicketOut(
        **ticket.model_dump(),
        category=normalized["category"],
        subcategory=normalized["subcategory"],
        priority=normalized["priority"],
        confidence=normalized["confidence"],
        reasoning=normalized["reasoning"],
        model_used=config.LLM_MODEL,
    )
