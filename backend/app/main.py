from __future__ import annotations

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import and_, or_, select, text
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Conversation, Message, Summary
from .schemas import (
    LANGUAGE_OPTIONS,
    AudioFinalizeIn,
    AudioPresignIn,
    AudioPresignOut,
    ConversationCreate,
    ConversationOut,
    MessageOut,
    MessagesListOut,
    SearchOut,
    SearchResultOut,
    SummaryIn,
    SummaryOut,
    TextMessageCreate,
)
from .services.provider_factory import get_ai_provider
from .services.storage import StorageService

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validate_language(code: str) -> None:
    if code not in LANGUAGE_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {code}")


def validate_role(role: str) -> None:
    if role not in {"doctor", "patient"}:
        raise HTTPException(status_code=400, detail="role must be doctor or patient")


def message_to_out(row: Message) -> MessageOut:
    return MessageOut(
        id=row.id,
        conversation_id=row.conversation_id,
        role=row.role,
        modality=row.modality,
        original_text=row.original_text,
        translated_text=row.translated_text,
        transcript_text=row.transcript_text,
        audio_url=row.audio_url,
        source_language=row.source_language,
        target_language=row.target_language,
        created_at=row.created_at,
    )


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "provider": settings.ai_provider}


@app.post("/api/conversations", response_model=ConversationOut)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)) -> ConversationOut:
    validate_language(payload.doctor_language)
    validate_language(payload.patient_language)

    conversation = Conversation(
        title=payload.title,
        doctor_language=payload.doctor_language,
        patient_language=payload.patient_language,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationOut.model_validate(conversation, from_attributes=True)


@app.get("/api/conversations/{conversation_id}", response_model=ConversationOut)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)) -> ConversationOut:
    row = db.get(Conversation, conversation_id)
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut.model_validate(row, from_attributes=True)


@app.get("/api/conversations/{conversation_id}/messages", response_model=MessagesListOut)
def list_messages(
    conversation_id: str,
    after_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MessagesListOut:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    base = select(Message).where(Message.conversation_id == conversation_id)

    if after_id:
        cursor = db.get(Message, after_id)
        if not cursor or cursor.conversation_id != conversation_id:
            raise HTTPException(status_code=400, detail="invalid_cursor")

        base = base.where(
            or_(
                Message.created_at > cursor.created_at,
                and_(Message.created_at == cursor.created_at, Message.id > cursor.id),
            )
        )
        query = base.order_by(Message.created_at.asc(), Message.id.asc()).limit(limit)
        rows = db.scalars(query).all()
    else:
        query = base.order_by(Message.created_at.desc(), Message.id.desc()).limit(limit)
        rows = list(reversed(db.scalars(query).all()))

    return MessagesListOut(items=[message_to_out(item) for item in rows])


@app.post("/api/messages/text", response_model=MessageOut)
async def send_text(payload: TextMessageCreate, db: Session = Depends(get_db)) -> MessageOut:
    validate_role(payload.role)
    validate_language(payload.source_language)
    validate_language(payload.target_language)

    if not db.get(Conversation, payload.conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Fail-open fallback for demo reliability: if provider fails/rate-limits,
    # still persist and return the message so chat flow is not blocked.
    try:
        provider = get_ai_provider()
        translated = await provider.translate(payload.text, payload.source_language, payload.target_language)
    except Exception:
        translated = payload.text

    row = Message(
        conversation_id=payload.conversation_id,
        role=payload.role,
        modality="text",
        original_text=payload.text,
        translated_text=translated,
        transcript_text=None,
        audio_url=None,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return message_to_out(row)


@app.post("/api/audio/presign", response_model=AudioPresignOut)
def presign_audio(payload: AudioPresignIn, db: Session = Depends(get_db)) -> AudioPresignOut:
    if not db.get(Conversation, payload.conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    if payload.mime_type not in settings.allowed_audio_mime_list:
        raise HTTPException(status_code=400, detail="Only audio/webm is supported")

    if not settings.s3_bucket:
        raise HTTPException(status_code=500, detail="S3 bucket is not configured")

    storage = StorageService()
    data = storage.presign_audio_upload(payload.conversation_id, payload.mime_type)
    return AudioPresignOut(**data)


@app.post("/api/messages/audio/finalize", response_model=MessageOut)
async def finalize_audio(payload: AudioFinalizeIn, db: Session = Depends(get_db)) -> MessageOut:
    validate_role(payload.role)
    validate_language(payload.source_language)
    validate_language(payload.target_language)

    if not db.get(Conversation, payload.conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
        audio_resp = await client.get(payload.audio_url)
        audio_resp.raise_for_status()
        audio_bytes = audio_resp.content

    max_bytes = settings.max_audio_mb * 1024 * 1024
    if len(audio_bytes) > max_bytes:
        raise HTTPException(status_code=400, detail="Audio file too large")

    # Fail-open fallback for demo reliability: keep audio message in thread
    # even if AI transcription/translation is temporarily unavailable.
    try:
        provider = get_ai_provider()
        transcript = await provider.transcribe_audio(audio_bytes, "audio/webm", payload.source_language)
        translated = await provider.translate(transcript, payload.source_language, payload.target_language)
    except Exception:
        transcript = "[Transcription unavailable]"
        translated = transcript

    row = Message(
        conversation_id=payload.conversation_id,
        role=payload.role,
        modality="audio",
        original_text=None,
        translated_text=translated,
        transcript_text=transcript,
        audio_url=payload.audio_url,
        source_language=payload.source_language,
        target_language=payload.target_language,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return message_to_out(row)


@app.get("/api/search", response_model=SearchOut)
def search(
    q: str = Query(min_length=1),
    conversation_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> SearchOut:
    dialect = db.bind.dialect.name

    if dialect == "postgresql":
        sql = """
        SELECT id, conversation_id, role, created_at,
               ts_headline('english',
                 coalesce(original_text,'') || ' ' || coalesce(transcript_text,'') || ' ' || coalesce(translated_text,''),
                 plainto_tsquery('english', :q)
               ) AS snippet
        FROM messages
        WHERE to_tsvector('english', coalesce(original_text,'') || ' ' || coalesce(transcript_text,'') || ' ' || coalesce(translated_text,''))
              @@ plainto_tsquery('english', :q)
          AND (:conversation_id IS NULL OR conversation_id = :conversation_id)
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
        """
        rows = db.execute(text(sql), {"q": q, "conversation_id": conversation_id, "limit": limit}).mappings().all()
    else:
        pattern = f"%{q}%"
        stmt = (
            select(Message)
            .where(
                or_(
                    Message.original_text.ilike(pattern),
                    Message.transcript_text.ilike(pattern),
                    Message.translated_text.ilike(pattern),
                )
            )
            .order_by(Message.created_at.desc(), Message.id.desc())
            .limit(limit)
        )
        if conversation_id:
            stmt = stmt.where(Message.conversation_id == conversation_id)
        items = db.scalars(stmt).all()
        rows = [
            {
                "id": row.id,
                "conversation_id": row.conversation_id,
                "role": row.role,
                "created_at": row.created_at,
                "snippet": (row.original_text or row.transcript_text or row.translated_text or "")[:220],
            }
            for row in items
        ]

    return SearchOut(
        items=[
            SearchResultOut(
                message_id=row["id"],
                conversation_id=row["conversation_id"],
                role=row["role"],
                created_at=row["created_at"],
                snippet=row["snippet"],
            )
            for row in rows
        ]
    )


@app.post("/api/conversations/{conversation_id}/summary", response_model=SummaryOut)
async def summarize(conversation_id: str, payload: SummaryIn, db: Session = Depends(get_db)) -> SummaryOut:
    if not db.get(Conversation, conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    ).all()

    lines: list[str] = []
    for msg in rows:
        source = msg.original_text or msg.transcript_text or ""
        translated = msg.translated_text or ""
        lines.append(f"[{msg.role}] original: {source}")
        lines.append(f"[{msg.role}] translated: {translated}")

    try:
        provider = get_ai_provider()
        parsed = await provider.summarize_medical(lines, payload.style)
    except ValueError:
        raise HTTPException(status_code=502, detail="summary_parse_failed")
    except RuntimeError as exc:
        detail = str(exc)
        if detail.endswith("_rate_limited"):
            raise HTTPException(status_code=429, detail=detail)
        raise HTTPException(status_code=502, detail=detail)
    except Exception:
        raise HTTPException(status_code=502, detail="gemini_unexpected_error")

    row = Summary(
        conversation_id=conversation_id,
        summary_text=parsed["summary"],
        symptoms_json=parsed["symptoms"],
        diagnoses_json=parsed["diagnoses"],
        medications_json=parsed["medications"],
        follow_up_json=parsed["follow_up"],
    )
    db.add(row)
    db.commit()

    return SummaryOut(
        summary=parsed["summary"],
        extracted={
            "symptoms": parsed["symptoms"],
            "diagnoses": parsed["diagnoses"],
            "medications": parsed["medications"],
            "follow_up": parsed["follow_up"],
        },
    )
