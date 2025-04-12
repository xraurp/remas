from pydantic import BaseModel
from src.db.models import Group, Limit, Task, TaskTag, Notification


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str

class UserNoPasswordSimple(BaseModel):
    id: int
    name: str | None
    surname: str | None
    username: str
    email: str
    uid: int

class UserNoPassword(UserNoPasswordSimple):
    group_id: int
    group: Group

    limits: list[Limit]
    tasks: list[Task]
    tags: list[TaskTag]
    created_notifications: list[Notification]
    notifications: list[Notification]
