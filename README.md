# Nao Medical - Doctor-Patient Translation Bridge

A full-stack web app that supports multilingual doctor-patient communication with text/audio messaging, search, and AI summaries.

## Status Update

Working now:
- Doctor/Patient role-based conversation workflow
- Conversation creation and persistence
- Text message send/receive with polling-based updates
- Search across conversation logs
- Summary generation endpoint and UI
- Audio recording/upload/finalize flow scaffolded

Important current behavior:
- AI provider is now configurable (`AI_PROVIDER=groq` or `gemini`).
- If translation provider fails/rate-limits, text messages still save and display.
- UI marks fallback messages with: `Translation fallback used (provider unavailable/rate-limited).`

## Features

Implemented:
- Two roles: Doctor and Patient
- Language selection (8 languages)
- Text messaging + translated output field
- Polling cursor semantics (`after_id`)
- Audio recording (`audio/webm`) and playable clips in thread
- Conversation persistence in SQL database
- Search endpoint + search page with context/highlight
- AI summary extraction (`symptoms`, `diagnoses`, `medications`, `follow_up`)
- Mobile-friendly interface

Known limitations/tradeoffs:
- No authentication (scope/timebox choice)
- Polling instead of WebSocket
- Audio requires S3-compatible bucket config
- Provider fallback may store original text as translated text when AI is unavailable
- Local SQLite used for fast development; Postgres recommended for production

## Tech Stack

Frontend:
- Next.js (App Router, TypeScript)
- React

Backend:
- FastAPI
- SQLAlchemy
- Pydantic Settings
- HTTPX
- Boto3 (S3 presigned uploads)

AI providers:
- Groq (current primary)
- Gemini (optional)

## Local Setup

Prerequisites:
- Python 3.12+
- Node.js 18+

1) Backend

```powershell
cd d:\nao_medical
.\env\Scripts\activate
pip install -r requirements.txt
Copy-Item backend\.env.example backend\.env
```

Set key env values in `backend/.env`:

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_key
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
DATABASE_URL=sqlite:///D:/nao_medical/nao_medical.db
```

Run backend:

```powershell
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

2) Frontend

```powershell
cd d:\nao_medical\frontend
npm install
Copy-Item .env.local.example .env.local
npm run dev
```

Ensure `frontend/.env.local` contains:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## API Overview

- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `GET /api/conversations/{id}/messages?after_id=<uuid>&limit=50`
- `POST /api/messages/text`
- `POST /api/audio/presign`
- `POST /api/messages/audio/finalize`
- `GET /api/search?q=<query>&conversation_id=<optional>`
- `POST /api/conversations/{id}/summary`

## Deployment Checklist

Backend (Render):
- Deploy FastAPI service
- Set backend env vars (`AI_PROVIDER`, provider keys, DB, CORS, S3)

Frontend (Vercel):
- Deploy Next.js app from `frontend/`
- Set `NEXT_PUBLIC_API_BASE_URL` to deployed backend URL

Smoke tests after deploy:
- Create conversation
- Send doctor message, see on patient tab
- Search keyword
- Generate summary
- Verify fallback indicator if provider quota is exhausted

## Security Note

Do not commit real API keys. Rotate any key that has been exposed during development.
