# Nao Medical - Doctor-Patient Translation Bridge

A full-stack healthcare communication app that helps a doctor and patient chat across languages with text/audio messages, searchable history, and AI-generated medical summaries.

## Live Links

- Frontend (Vercel): `https://nao-medical-five.vercel.app`
- Backend (Render): `https://nao-medical-t187.onrender.com`
- Repository: `https://github.com/Nojhi3/Nao_Medical`
- Example conversation: patient: `https://nao-medical-five.vercel.app/chat/4d4667f0-ad8a-4d34-ab50-799655f7155b?role=patient`
- Example conversation: doctor: `https://nao-medical-five.vercel.app/chat/4d4667f0-ad8a-4d34-ab50-799655f7155b?role=doctor`

## Project Overview

This project was built as a time-boxed MVP to satisfy the assignment requirements while prioritizing reliability and deployability.

Core capabilities include:
- Role-based chat (Doctor and Patient)
- Near real-time updates using polling
- Text translation between selected languages
- Browser audio recording + upload + playback
- Persistent conversation history
- Conversation search with highlighted matches
- AI summary extraction of clinically important information

## Features Completed

- `Doctor` and `Patient` role flows
- Conversation creation with role-specific shareable links
- Text message send + translated view
- Audio message recording (`audio/webm`) and in-thread playback
- Persistent messages and summaries in database
- Search endpoint + UI with context snippets
- AI summary endpoint + UI (`symptoms`, `diagnoses`, `medications`, `follow_up`)
- Mobile-friendly dark theme UI

## Technical Design

Frontend:
- Next.js (App Router, TypeScript)
- Polling with `after_id` cursor for near real-time updates

Backend:
- FastAPI + SQLAlchemy
- REST APIs for conversations/messages/audio/search/summary
- S3-compatible presigned uploads for audio

AI:
- Provider-configurable (`groq` primary, `gemini` optional)
- Fail-open behavior for message continuity when provider is unavailable/rate-limited

## API Endpoints

- `POST /api/conversations`
- `GET /api/conversations/{id}`
- `GET /api/conversations/{id}/messages?after_id=<uuid>&limit=50`
- `POST /api/messages/text`
- `POST /api/audio/presign`
- `POST /api/messages/audio/finalize`
- `GET /api/search?q=<query>&conversation_id=<optional>`
- `POST /api/conversations/{id}/summary`

## Local Setup

Prerequisites:
- Python 3.12+
- Node.js 18+

1. Backend

```powershell
cd d:\nao_medical
.\env\Scripts\activate
pip install -r requirements.txt
#initalize env file
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Frontend

```powershell
cd d:\nao_medical\frontend
npm install
#initalize env file
npm run dev
```

3. Frontend env (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Backend Environment Variables

Minimum (Groq + local dev):

```env
APP_ENV=development
DATABASE_URL=sqlite:///D:/nao_medical/nao_medical.db
AI_PROVIDER=groq
GROQ_API_KEY=...
GROQ_TRANSLATION_MODEL=llama-3.1-8b-instant
GROQ_SUMMARY_MODEL=llama-3.3-70b-versatile
GROQ_TRANSCRIBE_MODEL=whisper-large-v3-turbo
AI_TIMEOUT_SECONDS=20
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Audio/S3:

```env
S3_ENDPOINT_URL=https://s3.eu-north-1.amazonaws.com
S3_BUCKET=nao-medical-audio-prod
S3_REGION=eu-north-1
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_PUBLIC_BASE_URL=https://nao-medical-audio-prod.s3.eu-north-1.amazonaws.com
MAX_AUDIO_MB=15
ALLOWED_AUDIO_MIME=audio/webm
```

## Deployment

Backend (Render):
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Set all backend env vars in Render

Frontend (Vercel):
- Root directory: `frontend`
- Set env var:

```env
NEXT_PUBLIC_API_BASE_URL=https://YOUR_RENDER_BACKEND_URL
```

- Update backend CORS after Vercel URL is known:

```env
CORS_ORIGINS=https://nao-medical-five.vercel.app,https://www.nao-medical-five.vercel.app
```

## Known Limitations / Tradeoffs

- No authentication (assignment scope tradeoff)
- Polling used instead of WebSockets
- Audio restricted to `audio/webm`
- Translation can fallback to original text if provider is unavailable/rate-limited
- SQLite used for quick local setup; managed Postgres recommended for production

## AI Tools and Resources Used

- Groq API (translation, summarization, transcription)
- Gemini API (optional provider path)

## Final Checklist

- Create conversation and open doctor/patient links
- Send text both directions
- Record and play audio message
- Run search query and verify highlighted result
- Generate summary and verify extracted sections

