# AI Usage Note

**Project:** Ticket Auto-Categorization Webhook (Team 07, SD-02)
**AI Assistant Used:** Claude (Anthropic), via chat-based pair programming

---

## What AI Helped With

- **Scaffolding the whole project structure** in one pass: FastAPI app,
  Pydantic models, configuration module, classifier module, logger, tests,
  and documentation — saving most of the boilerplate-writing time on a
  1–2 day deadline.
- **Provider-agnostic LLM client design.** When our original API key setup
  stopped working, AI proposed and implemented a design where the LLM
  endpoint, model name, and key are all environment variables, as long as
  the provider speaks the OpenAI `chat/completions` format. This let us
  switch to Groq's free tier in minutes without touching application code.
- **Few-shot example set.** AI drafted 12 realistic IT service desk tickets
  spanning Hardware, Software, Network, Account & Access, Printing, and
  Infrastructure, with varied priorities, used to steer the classifier's
  category/subcategory taxonomy.
- **Robust JSON parsing.** AI wrote a small helper that extracts a JSON
  object from an LLM response even if it's wrapped in markdown fences or
  preceded by conversational text, plus a normalizer that clamps confidence
  to `[0, 1]` and falls back to `Medium` for invalid priority values.
- **Test suite.** AI wrote unit tests for the prompt-building / JSON-parsing
  logic that need no network access, and FastAPI `TestClient` tests for
  `/classify` and `/health` with the LLM call mocked — so the suite (and
  CI/grading) doesn't require a live API key.
- **Documentation**: README (setup, run, architecture, assumptions &
  limitations), `.env.example` covering multiple free providers, and this
  AI usage note.

## What AI Got Wrong / Needed Correction

- The first draft of `.env.example` only listed one provider (the one we
  originally tried, which had key issues). We asked AI to broaden it to
  several free, no-credit-card providers (Groq, OpenRouter, Gemini, Ollama)
  so the team isn't blocked again if one provider has issues.
- The initial few-shot set leaned toward "Critical" priority for almost
  every example; we asked AI to rebalance it across Low/Medium/High/Critical
  so the model learns a realistic priority distribution rather than always
  defaulting to the most urgent label.
- AI's first JSON-extraction approach assumed the model always returns
  clean JSON. We had to explicitly ask for the markdown-fence and
  "extra commentary" cases, since real LLM outputs aren't always clean —
  this is now covered by parametrized tests.
- Because this sandbox has no network access, AI could not actually run
  `pip install` or call a live LLM endpoint to verify end-to-end behavior.
  The pure-logic pieces (prompt building, JSON extraction, normalization)
  were unit-tested directly; the FastAPI/httpx integration follows standard,
  well-known patterns but should be smoke-tested locally with a real API key
  before the demo recording.

## Best Prompts Used

1. *"Make the LLM client work with any OpenAI-compatible chat completions
   endpoint, configured via environment variables, so I can switch
   providers without changing code."* — This single prompt avoided an
   entire class of "wrong SDK / wrong provider" problems.
2. *"LLMs sometimes wrap JSON in markdown fences or add extra commentary —
   add a helper that extracts JSON robustly and normalizes invalid
   priority/confidence values."* — Directly addressed reliability of
   structured output, which is one of the evaluation criteria.
3. *"Write tests that don't require a network connection or API key, by
   mocking the LLM call."* — Ensured the test suite (and therefore CI / a
   reviewer's quick check) works even without provider credentials.
