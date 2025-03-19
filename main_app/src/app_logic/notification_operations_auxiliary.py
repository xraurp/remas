from src.db.models import (
    Group,
    User,
    Notification,
    NotificationType
)
from src.schemas.notification_entities import GroupNotifications

def get_all_notifications_for_group(group: Group) -> list[GroupNotifications]:
    """
    Returns all notifications for group and parent groups.
    """
    notifications = [
        GroupNotifications(
            group_id=group.id,
            group_name=group.name,
            notifications=group.notifications
        )
    ]
    if group.parent:
        notifications += get_all_notifications_for_group(group=group.parent)
    return notifications

def get_all_notifications_for_user(user: User) -> list[GroupNotifications]:
    """
    Returns all notifications for user and his groups. Notifications asigned
    directly to user are returned without group information.
    """
    notifications = [
        GroupNotifications(
            group_id=None,
            group_name=None,
            notifications=user.notifications
        )
    ]
    notifications += get_all_notifications_for_group(group=user.group)
    return notifications

def get_user_notifications_by_type(
    types: list[NotificationType],
    user: User
) -> list[Notification]:
    """
    Returns all user notification with specified types.
    :param types (list[NotificationType]): types of notification to return
    :param user (User): user whose notifications to return
    :return (list[Notification]): notifications with tyven types
    """
    grouped_notifications = get_all_notifications_for_user(user=user)
    user_notifications = []
    for group in grouped_notifications:
        for notification in group.notifications:
            if notification.type not in types:
                continue
            # remove duplicates
            if notification in user_notifications:
                continue
            
            user_notifications.append(notification)
    return user_notifications
