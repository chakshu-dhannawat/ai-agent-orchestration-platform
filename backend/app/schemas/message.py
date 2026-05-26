import uuid
from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    from_agent: str
    to_agent: str
    content: str
    message_type: str
    metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}
