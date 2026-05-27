from datetime import datetime

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    config: dict = Field(default_factory=dict)
    agent_id: str | None = None
    workflow_id: str | None = None
    is_active: bool = True


class ChannelResponse(BaseModel):
    id: str
    type: str
    name: str
    config: dict
    agent_id: str | None
    workflow_id: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
