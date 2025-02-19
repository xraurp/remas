from pydantic import BaseModel
from src.db.models import Resource, Node, Group
from src.schemas.user_entities import UserNoPasswordSimple

class LimitResponse(BaseModel):
    id: int
    name: str
    description: str | None
    amount: int
    group: Group | None
    resource: Resource
    nodes: list[Node]

class LimitRequest(BaseModel):
    id: int | None = None
    name: str
    description: str | None = None
    amount: int
    user_id: int | None = None
    group_id: int | None = None
    resource_id: int
    node_ids: list[int]
