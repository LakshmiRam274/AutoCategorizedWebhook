"""
Helper script: runs every ticket in data/sample_tickets.json through the
running webhook and writes the enriched results to data/sample_outputs.json.

Usage:
    1. Start the API (in another terminal):
         uvicorn app.main:app --reload
    2. Run this script:
         python scripts/generate_sample_outputs.py
"""

import json
from pathlib import Path

import requests

API_URL = "http://127.0.0.1:8000/classify"
INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_tickets.json"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_outputs.json"


def main() -> None:
    tickets = json.loads(INPUT_FILE.read_text(encoding="utf-8"))

    results = []
    for ticket in tickets:
        print(f"Classifying {ticket['ticket_id']}...")
        resp = requests.post(API_URL, json=ticket, timeout=60)
        resp.raise_for_status()
        results.append(resp.json())

    OUTPUT_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {len(results)} results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
