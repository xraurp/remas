from pydantic import BaseModel
from src.schemas.user_entities import UserNoPasswordSimple
from src.schemas.task_entities import TaskResponseSimple

class TaskTagResponse(BaseModel):
    id: int
    name: str
    description: str | None
    user: UserNoPasswordSimple
    tasks: list[TaskResponseSimple]
