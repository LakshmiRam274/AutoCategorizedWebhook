#!/usr/bin/env bash
# Convenience script to start the API locally.
set -euo pipefail

if [ ! -f ".env" ]; then
  echo "No .env file found. Copying .env.example -> .env"
  echo "Edit .env and add your LLM API key before continuing."
  cp .env.example .env
  exit 1
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
