# Nao Medical - Doctor-Patient Translation Bridge

A full-stack web application that enables doctor-patient communication across languages using translated text and recorded audio.

## Project Overview

This app provides a near real-time translation workflow between two roles:
- Doctor
- Patient

Users can type or record messages, view translated outputs, search conversation history, and generate AI-assisted medical summaries.

## Features

Implemented:
- Role-based conversation flow (Doctor/Patient)
- Language selection (8 supported languages)
- Text translation pipeline (Gemini)
- Audio recording in browser (`audio/webm`)
- Presigned upload flow to S3-compatible storage
- Audio transcription + translation pipeline (Gemini)
- Persistent conversation/message storage
- Polling-based near real-time updates (`after_id` cursor)
- Search endpoint with PostgreSQL FTS (and SQLite fallback contains-search)
- Summary generation with structured sections:
  - symptoms
  - diagnoses
  - medications
  - follow_up
- Mobile-friendly responsive UI

Known limitations / tradeoffs:
- No authentication (assignment scope)
- Polling (2s) instead of WebSockets to reduce complexity risk
- Only `audio/webm` supported
- Summary JSON parsing is intentionally minimal (MVP)
- PostgreSQL FTS works best in production; local SQLite uses fallback text contains

## Tech Stack

Frontend:
- Next.js (App Router, TypeScript)
- React

Backend:
- FastAPI
- SQLAlchemy
- Pydantic Settings
- Boto3 (S3 presign/upload support)
- HTTPX

AI:
- Gemini API (translation, transcription, summary)

Data & Storage:
- PostgreSQL (target production DB)
- SQLite (local default for quick startup)
- S3-compatible object storage for audio

Deployment target:
- Frontend: Vercel
- Backend + DB: Render

## Repository Structure

```text
.
|- backend/
|  |- app/
|  |  |- main.py
|  |  |- models.py
|  |  |- schemas.py
|  |  |- services/
|  |     |- gemini.py
|  |     |- storage.py
|  |- .env.example
|- frontend/
|  |- src/app/
|  |  |- page.tsx
|  |  |- chat/[id]/page.tsx
|  |  |- search/page.tsx
|  |- src/lib/api.ts
|- requirements.txt
|- README.md
```

## Local Setup

## 1) Prerequisites
- Python 3.12+
- Node.js 18+
- npm

## 2) Backend setup
From repo root:

```powershell
.\env\Scripts\activate
pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
```

Fill `backend/.env`:
- `AI_PROVIDER=gemini`
- `GEMINI_API_KEY=<your_key>`
- DB + S3 values for full functionality

Run backend:

```powershell
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3) Frontend setup

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Set `frontend/.env.local`:
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

Frontend runs on `http://localhost:3000`.

## API Summary

- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `GET /api/conversations/{id}/messages?after_id=<uuid>&limit=50`
- `POST /api/messages/text`
- `POST /api/audio/presign`
- `POST /api/messages/audio/finalize`
- `GET /api/search?q=<query>&conversation_id=<optional>`
- `POST /api/conversations/{id}/summary`

## Polling Semantics

- Client polls every 2 seconds.
- Cursor uses `after_id` (UUID), not timestamp.
- Server returns messages ordered by `(created_at ASC, id ASC)`.
- Invalid cursor returns `400 invalid_cursor`.
- Frontend backs off to 4s polling after repeated failures.

## AI Tools / Resources Leveraged

- Gemini API for:
  - text translation
  - audio transcription
  - structured conversation summarization

## Submission Notes

This implementation is intentionally lean to maximize reliability under a 12-hour assignment window while preserving strong full-stack and AI-integration hiring signal.
