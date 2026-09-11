# AI Media Intelligence - Demo Runbook

## Start

Run:

.\start-media-intelligence.ps1

## Readiness Check

Run:

.\check-media-intelligence.ps1

Expected:

SYSTEM READY FOR DEMO

## Dashboard

http://localhost:3000

Demo order:
1. Overview
2. Intelligence
3. Risk Analytics
4. Alerts & SLA
5. Companies

## Core Services

- PostgreSQL: 127.0.0.1:5432
- Redis: 127.0.0.1:6379
- Ollama: 127.0.0.1:11434
- FastAPI: 127.0.0.1:8000
- Dashboard: localhost:3000
- Celery queue: media-intelligence
- Local LLM: qwen2.5:7b
- Embeddings: all-MiniLM-L6-v2

## Intelligence Pipeline

News Sources
→ Collection
→ Extraction
→ Normalization
→ Deduplication
→ Embeddings
→ Semantic Relevance
→ Local LLM Triage
→ Business Rules
→ Risk Engine
→ Insight Agent
→ Alert Persistence
→ Celery
→ Slack
→ Dashboard

## Slack

Channel:

#media-intelligence-alerts

The Slack webhook is stored only in the private root .env file.

Never commit or share the webhook URL.

## Stop

Run:

.\stop-media-intelligence.ps1

This stops FastAPI, Celery, and Next.js.
