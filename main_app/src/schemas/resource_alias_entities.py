from pydantic import BaseModel
from src.db.models import Resource

class AliasResponse(BaseModel):
    id: int
    name: str
    description: str | None
    resources: list[Resource]
