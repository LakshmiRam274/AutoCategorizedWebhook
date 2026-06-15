# Ticket Auto-Categorization Webhook

A small FastAPI service for an IT/Service Desk: it receives a raw support
ticket as JSON, uses an LLM (with few-shot examples) to classify its
**category**, **subcategory**, and **priority**, and returns the ticket
enriched with that classification. Every prediction is logged for monitoring.

Built for the Infinite Computer Solutions AI Prototype Challenge — Team 07
(SD-02, Service Desk: Auto-Categorization Webhook).

---

## 1. Architecture Overview

```
                ┌─────────────────────┐
  POST /classify│                     │  1. Load few-shot examples
 ─────────────► │   FastAPI webhook   │     from data/samples.json
  ticket JSON   │   (app/main.py)     │
                │                     │  2. Build prompt (system +
                └──────────┬──────────┘     few-shot + new ticket)
                           │
                           ▼
                ┌─────────────────────┐
                │  app/classifier.py  │  3. Call any OpenAI-compatible
                │  (prompt building,  │     LLM endpoint via httpx
                │   JSON parsing,     │     (Groq / OpenRouter / Gemini /
                │   normalization)    │      Ollama / etc.)
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
  enriched JSON │  app/logger.py      │  4. Append prediction record
 ◄───────────── │  (JSONL monitoring  │     to logs/predictions.jsonl
                │   log)              │
                └─────────────────────┘
```

**Request flow**

1. A client (Service Desk system, Postman, curl, etc.) sends a ticket as
   JSON to `POST /classify`.
2. `app/classifier.py` loads a handful of pre-labeled example tickets from
   `data/samples.json` and builds a chat prompt: a system instruction
   describing the schema, the few-shot examples, and the new ticket.
3. The prompt is sent to **any OpenAI-compatible chat-completions endpoint**
   (configured purely via environment variables — see [Configuration](#3-configuration)).
4. The model's JSON reply is parsed and normalized (invalid priorities /
   out-of-range confidence values are corrected to safe defaults).
5. The original ticket fields plus `category`, `subcategory`, `priority`,
   `confidence`, `reasoning`, and `model_used` are returned to the caller,
   and the same record is appended to `logs/predictions.jsonl` for
   monitoring/auditing.

### Project layout

```
.
├── app/
│   ├── main.py        # FastAPI app & /classify endpoint
│   ├── classifier.py  # Prompt building, LLM call, JSON parsing
│   ├── models.py      # Pydantic request/response models
│   ├── logger.py       # JSONL prediction logging
│   └── config.py      # Env-based configuration
├── data/
│   ├── samples.json             # Few-shot examples used in every prompt
│   ├── sample_tickets.json       # Example input tickets
│   └── expected_output_example.json  # Illustrative response shape
├── scripts/
│   └── generate_sample_outputs.py   # Runs sample_tickets.json through the API
├── tests/
│   ├── test_classifier.py   # Unit tests (no network / API key needed)
│   └── test_api.py          # API tests with the LLM call mocked out
├── notes/
│   └── prompts.md      # Key prompts used during development (AI usage)
├── docs/
│   └── AI_USAGE_NOTE.md
├── logs/                # predictions.jsonl written here at runtime
├── requirements.txt
├── .env.example
└── README.md
```

---

## 2. Setup Instructions

### Prerequisites

- Python 3.10+
- A **free** API key from any OpenAI-compatible LLM provider (see below)

### Steps

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd ticket-categorization-webhook

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your LLM provider
cp .env.example .env
# then edit .env and paste in your API key (see Configuration below)
```

---

## 3. Configuration

This project does **not** hard-code a specific LLM provider. Instead, it
talks to any provider that implements an OpenAI-compatible
`POST {LLM_BASE_URL}/chat/completions` endpoint, configured via three
environment variables: `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`.

> If your usual provider's key/SDK isn't working, just pick a different
> free provider below — no code changes needed, only `.env` changes.

| Provider | Cost | `LLM_BASE_URL` | `LLM_MODEL` example | Get a key |
|---|---|---|---|---|
| **Groq** (recommended) | Free, no card | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` | https://console.groq.com/keys |
| **OpenRouter** | Free models available | `https://openrouter.ai/api/v1` | `meta-llama/llama-3.1-8b-instruct:free` | https://openrouter.ai/keys |
| **Google Gemini** | Free tier | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-1.5-flash` | https://aistudio.google.com/apikey |
| **Ollama** (local, offline) | Free | `http://localhost:11434/v1` | `llama3.1` | n/a — `ollama pull llama3.1` |

See `.env.example` for ready-to-uncomment blocks for each provider.

---

## 4. Run Instructions

### Start the API

```bash
uvicorn app.main:app --reload
```

The service starts on `http://127.0.0.1:8000`. Interactive API docs (Swagger
UI) are available at `http://127.0.0.1:8000/docs`.

### Call the webhook

```bash
curl -X POST http://127.0.0.1:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
        "ticket_id": "TCK-3001",
        "subject": "Cannot login to VPN",
        "description": "I cannot connect to the corporate VPN since this morning, getting an authentication error.",
        "requester": "rohan.mehta@example.com"
      }'
```

Example response:

```json
{
  "ticket_id": "TCK-3001",
  "subject": "Cannot login to VPN",
  "description": "I cannot connect to the corporate VPN since this morning, getting an authentication error.",
  "requester": "rohan.mehta@example.com",
  "metadata": null,
  "category": "Network",
  "subcategory": "VPN Access",
  "priority": "High",
  "confidence": 0.93,
  "reasoning": "VPN authentication failure is blocking access ahead of a time-sensitive call.",
  "model_used": "llama-3.1-8b-instant"
}
```

### Generate sample outputs

With the server running, populate `data/sample_outputs.json` by classifying
every ticket in `data/sample_tickets.json`:

```bash
python scripts/generate_sample_outputs.py
```

### View monitoring logs

Every prediction is appended as one JSON line to `logs/predictions.jsonl`:

```bash
tail -f logs/predictions.jsonl
```

---

## 5. Running Tests

```bash
pytest -v
```

- `tests/test_classifier.py` — unit tests for prompt building, JSON
  extraction, and result normalization. **No network or API key required.**
- `tests/test_api.py` — end-to-end API tests with the LLM call mocked, so
  they also run without a network connection or API key.

---

## 6. Assumptions & Limitations

- **Assumption**: the configured LLM provider implements the standard
  OpenAI `chat/completions` request/response shape. Most modern free
  providers (Groq, OpenRouter, Gemini's OpenAI-compat endpoint, Ollama) do.
- **Assumption**: tickets are in English and contain at least a `subject`
  and `description`.
- The taxonomy of categories/subcategories is *learned implicitly* from the
  few-shot examples in `data/samples.json` — it is not a hard-coded enum.
  Adding/editing examples there will steer (and can expand) the taxonomy
  without any code changes.
- `priority` is constrained to `Low | Medium | High | Critical`; if the
  model returns anything else it is corrected to `Medium`.
- `confidence` is the model's *self-reported* confidence (clamped to
  `0.0–1.0`) — it is not a calibrated probability.
- This is a **1–2 day prototype**: there is no authentication, rate
  limiting, retry/backoff, or persistent database. The prediction log is a
  flat JSONL file, suitable for a demo but not for production-scale
  monitoring.
- If the LLM response cannot be parsed as JSON at all, the endpoint returns
  `HTTP 502` with details of the failure rather than guessing a
  classification.
