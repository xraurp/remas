from pydantic import BaseModel
from src.db.models import Node, ResourceAlias


class ResourceResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    providing_nodes: list[Node] = []
    aliases: list[ResourceAlias]
