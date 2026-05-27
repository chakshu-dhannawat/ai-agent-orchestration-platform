from datetime import datetime

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    id: str
    execution_id: str
    from_agent: str
    to_agent: str
    content: str
    message_type: str
    metadata: dict | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
