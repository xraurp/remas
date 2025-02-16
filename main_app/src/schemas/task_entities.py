from src.db.models import (
    Task,
    TaskTag,
    ResourceAllocation,
    Node,
    Resource,
    Event,
    User
)
from datetime import datetime
from pydantic import BaseModel
from src.schemas.user_entities import UserNoPasswordSimple


class TaskResourceAllocationResponse(BaseModel):
    node: Node
    resource: Resource
    amount: int

class TaskResponseBase(BaseModel):
    id: int
    name: str
    description: str | None
    start_time: datetime
    end_time: datetime
    status: str

class TaskResponseSimple(TaskResponseBase):
    owner: UserNoPasswordSimple

class TaskResponseFull(TaskResponseBase):
    tags: list[TaskTag]
    resources: list[TaskResourceAllocationResponse]

class TaskResponseFullWithOwner(TaskResponseFull):
    owner: UserNoPasswordSimple

class ResourceAllocationRequest(BaseModel):
    node_id: int
    resource_id: int
    amount: int

class CreateTaskRequest(BaseModel):
    id: int | None
    name: str
    description: str | None
    tag_ids: list[int]
    resource_allocations: list[ResourceAllocationRequest]
    start_time: datetime
    end_time: datetime
