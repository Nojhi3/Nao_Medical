from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doctor_language: Mapped[str] = mapped_column(String(16), nullable=False)
    patient_language: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

    messages: Mapped[list[Message]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    summaries: Mapped[list[Summary]] = relationship("Summary", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    modality: Mapped[str] = mapped_column(String(16), nullable=False)

    original_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_language: Mapped[str] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)

    symptoms_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    diagnoses_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    medications_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    follow_up_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="summaries")


Index("ix_messages_conversation_created_id", Message.conversation_id, Message.created_at, Message.id)
