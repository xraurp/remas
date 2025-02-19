from pydantic import BaseModel
from src.db.models import Notification


class AssignNotificationRequest(BaseModel):
    notification_id: int
    user_id: int
    group_id: int

class GroupNotifications(BaseModel):
    group_id: int
    group_name: str
    notifications: list[Notification]
