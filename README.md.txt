Auto Ticket Categorization Webhook

Architecture Overview

The project is built using FastAPI. The API receives support tickets, analyzes the ticket text, and automatically assigns a category based on predefined keywords. The categorized result is then returned as a JSON response.

Categories

- Access Issue
- Billing
- Technical Issue
- General Query

Technologies Used

- Python
- FastAPI
- Uvicorn

Setup Instructions

1. Install Python
2. Install FastAPI and Uvicorn:
   pip install fastapi uvicorn

Run Instructions

uvicorn app:app --reload

API Endpoint

POST /categorize

Sample Input

{
"text": "I forgot my password and cannot login"
}

Sample Output

{
"category": "Access Issue"
}

Assumptions

- Tickets are written in English.
- Categories are assigned using keyword matching.
- Each ticket belongs to one primary category.

Limitations

- The system is rule-based and not powered by a machine learning model.
- Complex or ambiguous tickets may be categorized incorrectly.
- Supports only predefined categories.
