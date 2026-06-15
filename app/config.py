"""
Central configuration for the Auto-Categorization Webhook.

The classifier talks to ANY OpenAI-compatible "chat completions" endpoint.
This means you can point it at Groq, OpenRouter, Google Gemini (OpenAI-compat
endpoint), a local Ollama instance, or any other provider that implements the
same `/chat/completions` shape -- just by changing environment variables.
No code changes are needed to switch providers.

Recommended FREE providers (no credit card required):
  - Groq        -> https://console.groq.com/keys
  - OpenRouter  -> https://openrouter.ai/keys   (look for models tagged ":free")
  - Gemini      -> https://aistudio.google.com/apikey (OpenAI-compat endpoint)
  - Ollama      -> fully local, no key needed at all
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file if present (never commit this file).
load_dotenv()

# --- LLM provider configuration -------------------------------------------------
# Base URL of the OpenAI-compatible API (WITHOUT a trailing slash, no /chat/completions).
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")

# Model name as understood by the chosen provider.
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# API key for the chosen provider. For Ollama this can be any non-empty string.
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")

# Request timeout (seconds) for the LLM call.
LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30"))

# Whether to ask the provider for strict JSON output via response_format.
# Most OpenAI-compatible providers (Groq, OpenRouter, Gemini) support this;
# if a provider rejects the parameter the client automatically retries
# without it, so it is safe to leave enabled.
LLM_JSON_MODE: bool = os.getenv("LLM_JSON_MODE", "true").lower() in {"1", "true", "yes"}

# --- Application data / logging --------------------------------------------------
# Few-shot examples used to steer the classifier.
SAMPLES_FILE: str = os.getenv("SAMPLES_FILE", "data/samples.json")

# Where prediction logs (JSON Lines) are written for monitoring.
LOG_FILE: str = os.getenv("LOG_FILE", "logs/predictions.jsonl")

# Allowed priority values returned by the classifier.
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]

# Default fallbacks used if the LLM response is malformed.
DEFAULT_CATEGORY = "Uncategorized"
DEFAULT_SUBCATEGORY = "General"
DEFAULT_PRIORITY = "Medium"
