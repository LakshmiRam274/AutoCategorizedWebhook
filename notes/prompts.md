# Development Prompts Log

This file lists the key prompts used with an AI coding assistant (Claude)
while building the Ticket Auto-Categorization Webhook, in roughly the order
they were used. Kept simple as per the challenge's "Prompt Documentation"
requirement.

---

### 1. Initial scaffold
> "Build a FastAPI webhook that receives a service desk ticket as JSON
> (ticket_id, subject, description), uses an LLM to classify
> category/subcategory/priority, and returns the enriched ticket as JSON.
> Load few-shot examples from data/samples.json."

### 2. Provider flexibility (the API key issue)
> "My usual LLM API key isn't working. Make the LLM client work with any
> OpenAI-compatible chat completions endpoint, configured via environment
> variables, so I can switch to a different free provider (Groq,
> OpenRouter, Gemini, Ollama) without changing code."

### 3. Few-shot prompt design
> "Write the system prompt and few-shot example formatting so the model
> always returns a single JSON object with category, subcategory, priority,
> confidence, and reasoning — and create ~10-12 realistic IT service desk
> example tickets covering Hardware, Software, Network, Account & Access,
> Printing, and Infrastructure, with a range of priorities."

### 4. Robust JSON parsing
> "LLMs sometimes wrap JSON in markdown fences or add extra commentary.
> Add a helper that extracts a JSON object from the raw model response
> robustly, and normalize/validate the priority and confidence fields with
> sensible defaults if the model returns something unexpected."

### 5. Monitoring/logging
> "Log every request/response pair (ticket id, input, classification,
> latency) as JSON Lines to logs/predictions.jsonl for monitoring."

### 6. Tests
> "Write pytest tests: unit tests for the prompt-building and JSON-parsing
> helpers that need no network access, plus FastAPI TestClient tests for
> /classify and /health with the LLM call mocked out so the test suite runs
> without an API key."

### 7. Documentation
> "Write a README with setup instructions, run instructions, an
> architecture overview, and an assumptions & limitations section. Also
> write a 1-page AI usage note covering what the AI helped with, what it
> got wrong, and the best prompts used."

---

## What changed after AI's first draft (manual review)

- Verified the OpenAI-compatible `/chat/completions` shape works across
  Groq, OpenRouter, and Gemini's compatibility endpoint so the provider can
  be swapped via `.env` only.
- Reviewed and hand-edited the few-shot examples in `data/samples.json` for
  realism and to ensure priority levels were sensibly distributed
  (not everything "Critical").
- Confirmed the JSON-extraction fallback regex doesn't false-positive on
  nested braces in `reasoning` text.
