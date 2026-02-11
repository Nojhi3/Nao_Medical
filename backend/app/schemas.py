from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Role = Literal["doctor", "patient"]
Modality = Literal["text", "audio"]

LANGUAGE_OPTIONS = ["en", "es", "zh", "ar", "hi", "bn", "pt", "ru"]


class ConversationCreate(BaseModel):
    doctor_language: str
    patient_language: str
    title: str | None = None


class ConversationOut(BaseModel):
    id: str
    title: str | None
    doctor_language: str
    patient_language: str
    created_at: datetime


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: Role
    modality: Modality
    original_text: str | None
    translated_text: str | None
    transcript_text: str | None
    audio_url: str | None
    source_language: str
    target_language: str
    created_at: datetime


class TextMessageCreate(BaseModel):
    conversation_id: str
    role: Role
    text: str = Field(min_length=1)
    source_language: str
    target_language: str


class AudioPresignIn(BaseModel):
    conversation_id: str
    mime_type: str


class AudioPresignOut(BaseModel):
    upload_url: str
    file_url: str
    object_key: str


class AudioFinalizeIn(BaseModel):
    conversation_id: str
    role: Role
    audio_url: str
    source_language: str
    target_language: str


class MessagesListOut(BaseModel):
    items: list[MessageOut]


class SearchResultOut(BaseModel):
    message_id: str
    conversation_id: str
    role: Role
    created_at: datetime
    snippet: str


class SearchOut(BaseModel):
    items: list[SearchResultOut]


class SummaryIn(BaseModel):
    style: Literal["concise", "clinical"] = "concise"


class SummaryOut(BaseModel):
    summary: str
    extracted: dict


class ApiError(BaseModel):
    code: str
    detail: str
