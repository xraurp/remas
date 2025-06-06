from pydantic import BaseModel
from src.db.models import Node, ResourceAlias


class ResourceResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    unit: str
    providing_nodes: list[Node] = []
    aliases: list[ResourceAlias]

class AliasRequest(BaseModel):
    resource_id: int
    alias_id: int
