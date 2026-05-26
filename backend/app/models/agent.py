import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o-mini")
    tools: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    channels: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    schedule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    memory_window: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    interaction_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    guardrails: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=4096)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    channel_configs = relationship("Channel", back_populates="agent", cascade="all, delete-orphan")
