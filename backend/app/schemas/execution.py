from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionCreate(BaseModel):
    workflow_id: str
    input_data: dict = Field(default_factory=dict)


class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: str
    input_data: dict
    output_data: dict | None
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    current_node: str | None
    error: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionLogResponse(BaseModel):
    id: str
    execution_id: str
    level: str
    node_id: str | None
    agent_name: str | None
    message: str
    metadata: dict | None = Field(default=None, validation_alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
