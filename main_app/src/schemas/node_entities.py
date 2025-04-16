from pydantic import BaseModel

class NodeResourceResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    unit: str
    amount: int

class NodeResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    resources: list[NodeResourceResponse] = []

class NodeProvidesResourceRequest(BaseModel):
    resource_id: int
    node_id: int
    amount: int
