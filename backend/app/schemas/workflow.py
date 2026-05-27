from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    is_template: bool = False
    template_id: str | None = None
    graph_definition: dict = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    is_template: bool | None = None
    graph_definition: dict | None = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    is_template: bool
    template_id: str | None
    graph_definition: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
