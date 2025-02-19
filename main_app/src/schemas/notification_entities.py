from pydantic import BaseModel
from src.db.models import Notification


class AssignNotificationRequest(BaseModel):
    notification_id: int
    user_id: int | None = None
    group_id: int | None = None

class GroupNotifications(BaseModel):
    group_id: int | None
    group_name: str | None
    notifications: list[Notification]
