import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_template: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    template_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    graph_definition: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    executions = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )
    channel_configs = relationship(
        "Channel", back_populates="workflow", cascade="all, delete-orphan"
    )
