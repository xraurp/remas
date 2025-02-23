from pydantic import BaseModel
from typing import Optional
from src.db.models import User, Limit, Group, Notification
from src.schemas.user_entities import UserNoPasswordSimple

class GroupResponse(BaseModel):
    id: int
    name: str
    description: str | None
    users_share_statistics: bool

    # Self reference - parent / child relationship
    parent: Optional[Group]
    children: list[Group]

    members: list[UserNoPasswordSimple]
    limits: list[Limit]
    notifications: list[Notification]

class UserGroupChangeRequest(BaseModel):
    user_id: int
    group_id: int

class GroupChangeParentRequest(BaseModel):
    group_id: int
    parent_id: int
