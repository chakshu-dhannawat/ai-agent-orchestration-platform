from datetime import datetime

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=255)
    system_prompt: str = ""
    model: str = "gpt-4o-mini"
    tools: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    schedule: dict | None = None
    memory_enabled: bool = True
    memory_window: int = Field(default=20, ge=1, le=100)
    skills: list[str] = Field(default_factory=list)
    interaction_rules: dict = Field(default_factory=dict)
    guardrails: dict = Field(default_factory=dict)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=128000)


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: str | None = Field(default=None, min_length=1, max_length=255)
    system_prompt: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    channels: list[str] | None = None
    schedule: dict | None = None
    memory_enabled: bool | None = None
    memory_window: int | None = Field(default=None, ge=1, le=100)
    skills: list[str] | None = None
    interaction_rules: dict | None = None
    guardrails: dict | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)


class AgentResponse(BaseModel):
    id: str
    name: str
    role: str
    system_prompt: str
    model: str
    tools: list
    channels: list
    schedule: dict | None
    memory_enabled: bool
    memory_window: int
    skills: list
    interaction_rules: dict
    guardrails: dict
    temperature: float
    max_tokens: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
