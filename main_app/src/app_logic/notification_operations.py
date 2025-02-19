from src.db.models import (
    Notification,
    User,
    Group,
    NotificationType,
    Event,
    EventType
)
from sqlmodel import select, Session
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound
from src.schemas.notification_entities import (
    AssignNotificationRequest,
    GroupNotifications
)
from datetime import datetime, timedelta

def get_all_notifications(db_session: Session) -> list[Notification]:
    """
    Returns all notifications
    """
    return db_session.scalars(select(Notification)).all()

def get_notification(notification_id: int, db_session: Session) -> Notification:
    """
    Returns notification by id
    """
    try:
        return db_session.scalars(
            select(Notification).where(Notification.id == notification_id)
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {notification_id} not found!"
        )

def create_notification(
    notification: Notification,
    user_id: int,
    db_session: Session
) -> Notification:
    """
    Creates new notification
    """
    notification.id = None
    notification.owner_id = user_id
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification

def remove_notification(notification_id: int, db_session: Session) -> None:
    """
    Removes notification
    """
    notification = db_session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {notification_id} not found!"
        )
    db_session.delete(notification)
    db_session.commit()

def update_notification(
    notification: Notification,
    user_id: int,
    db_session: Session
) -> Notification:
    """
    Updates notification
    """
    db_notification = db_session.get(Notification, notification.id)
    if not db_notification:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {notification.id} not found!"
        )
    # TODO - check admin
    if db_notification.owner_id != user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't update notification owned by another user!"
        )
    
    reschedule = False
    if notification.type != db_notification.type \
    or notification.time_offset != db_notification.time_offset:
        reschedule = True

    db_notification.name = notification.name
    db_notification.description = notification.description
    db_notification.time_offset = notification.time_offset
    db_notification.type = notification.type
    db_notification.notification_content = notification.notification_content
    db_session.commit()
    db_session.refresh(db_notification)
    # reschedule notification after update
    if reschedule:
        reschedule_notification_events_for_all(
            notification=db_notification,
            session=db_session
        )
        db_session.commit()
        db_session.refresh(db_notification)
    return db_notification

def assign_or_unassign_notification(
    assignment_request: AssignNotificationRequest,
    db_session: Session,
    unassign: bool = False
) -> Notification:
    """
    Assigns / unassignes notification to/from user or group in the request.
    :param assignment_request (AssignNotificationRequest): request with id of
        group or user to which notification will be assigned / removed from
    :param db_session (Session): database session to use
    :param unassign (bool): tells if the notification should be assigned to the
        user / group or if notificaton they already have should be unassigned
        from them
    :return (Notification): modified notification
    """
    if not assignment_request.user_id and not assignment_request.group_id:
        raise HTTPException(
            status_code=400,
            detail="Either user_id or group_id must be specified!"
    )
    db_notification = db_session.get(
        Notification,
        assign_notification.notification_id
    )
    if not db_notification:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {assignment_request.notification_id}"
                    " not found!"
        )
    
    if assignment_request.user_id:
        user = db_session.get(User, assignment_request.user_id)
        if not user:
            raise HTTPException(
                status_code=404,
                detail=f"User with id {assignment_request.user_id} not found!"
            )
    else:
        user = None
    
    if assignment_request.group_id:
        group = db_session.get(Group, assignment_request.group_id)
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Group with id {assignment_request.group_id} not found!"
            )
    else:
        group = None
    
    if unassign:
        if user and user in db_notification.receivers_users:
            db_notification.receivers_users.remove(user)
            remove_notification_scheduling_for_user(
                notification=db_notification,
                user=user,
                db_session=db_session
            )
        if group and group in db_notification.receivers_groups:
            db_notification.receivers_groups.remove(group)
            remove_notification_scheduling_for_group(
                notification=db_notification,
                group=group,
                db_session=db_session
            )
    else:
        if user and user not in db_notification.receivers_users:
            db_notification.receivers_users.append(user)
            schedule_notification_events_for_user(
                notification=db_notification,
                user=user,
                db_session=db_session
            )
        if group and group not in db_notification.receivers_groups:
            db_notification.receivers_groups.append(group)
            schedule_notitifation_events_for_group(
                notification=db_notification,
                group=group,
                db_session=db_session
            )
    
    db_session.commit()
    db_session.refresh(db_notification)
    return db_notification

def schedule_notification_events_for_task(
    notification: Notification,
    task: Task,
    db_session: Session
) -> None:
    """
    Schedules notification events for task.
    Does not commit changes in database!
    """
    # check if notification needs to be scheduled
    if notification.type \
    not in (NotificationType.task_start, NotificationType.task_end):
        return

    scheduled_event = None
    # check if notification is scheduled already
    for event in task.events:
        if event.notification == notification:
            scheduled_event = event
            break
    
    # determine time when notification should be send
    if notification.type == NotificationType.task_start:
        # do not schedule notification for start time
        # if task is has already started
        if task.status != TaskStatus.scheduled:
            return
        start = task.start_time + timedelta(seconds=notification.time_offset)
        event_type = EventType.task_start
    else:
        # do not schedule notification for end time
        # if task is has already finished
        if task.status == TaskStatus.finished:
            return
        start = task.end_time + timedelta(seconds=notification.time_offset)
        event_type = EventType.task_end
    
    # schedule the notification
    if scheduled_event:
        # reschedule existing
        if scheduled_event.time != start:
            scheduled_event.time = start
            scheduled_event.type = event_type
    else:
        # schedule new
        scheduled_event = Event(
            id = None,
            name = f"Task: {task.name}, notification: {notification.name}",
            time = start,
            type = event_type,
            taks_id = task.id,
            notification_id = notification.id
        )
        db_session.add(scheduled_event)

def schedule_notification_events_for_user(
    notification: Notification,
    user: User,
    db_session: Session
) -> Notification:
    """
    Schedule notification events for user.
    Does not commit changes in database!
    """
    # check if notification needs to be scheduled
    if notification.type \
    not in (NotificationType.user_start, NotificationType.user_end):
        return

    for task in user.tasks:
        schedule_notification_events_for_task(
            notification=notification,
            task=task,
            db_session=db_session
        )

def schedule_notitifation_events_for_group(
    notification: Notification,
    group: Group,
    db_session: Session
) -> None:
    """
    Schedule notification events for group.
    Does not commit changes in database!
    """
    # check if notification needs to be scheduled
    if notification.type \
    not in (NotificationType.user_start, NotificationType.user_end):
        return
    
    for user in group.members:
        schedule_notification_events_for_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
    
    for subgroup in group.children:
        schedule_notitifation_events_for_group(
            notification=notification,
            group=subgroup,
            db_session=db_session
        )

def reschedule_notification_events_for_all(
    notification: Notification,
    db_session: Session
) -> None:
    """
    Reschedules notification events for all groups and users.
    Does not commit changes in database!
    """
    # check if notification needs to be scheduled
    if notification.type \
    not in (NotificationType.user_start, NotificationType.user_end):
        return
    
    for user in notification.receivers_users:
        schedule_notification_events_for_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
    
    for group in notification.receivers_groups:
        schedule_notification_events_for_group(
            notification=notification,
            group=group,
            db_session=db_session
        )

def remove_notification_scheduling_for_task(
    notification: Notification,
    task: Task,
    db_session: Session
) -> None:
    """
    Removes notification scheduling for task.
    Does not commit changes in database!
    """
    for event in notification.events:
        if event.task == task:
            db_session.delete(event)

def remove_notification_scheduling_for_user(
    notification: Notification,
    user: User,
    db_session: Session
) -> None:
    """
    Removes notification scheduling for user.
    Does not commit changes in database!
    """
    for task in user.tasks:
        remove_notification_scheduling_for_task(
            notification=notification,
            task=task,
            db_session=db_session
        )

def remove_notification_scheduling_for_group(
    notification: Notification,
    group: Group,
    db_session: Session
) -> None:
    """
    Removes notification scheduling for group.
    Does not commit changes in database!
    """
    for user in group.members:
        remove_notification_scheduling_for_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
    
    for subgroup in group.children:
        remove_notification_scheduling_for_group(
            notification=notification,
            group=subgroup,
            db_session=db_session
        )

def remove_notification_scheduling_for_all(
    notification: Notification,
    db_session: Session
) -> None:
    """
    Removes notification scheduling for all groups and users.
    Does not commit changes in database!
    """
    for user in notification.receivers_users:
        remove_notification_scheduling_for_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
    
    for group in notification.receivers_groups:
        remove_notification_scheduling_for_group(
            notification=notification,
            group=group,
            db_session=db_session
        )

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

def get_notifications_by_group_id(
    group_id: int,
    db_session: Session
) -> list[GroupNotifications]:
    """
    Returns notifications by group id
    """
    group = db_session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group_id} not found!"
        )
    return get_all_notifications_for_group(group=group)

def get_notifications_by_user_id(
    user_id: int,
    db_session: Session
) -> list[GroupNotifications]:
    """
    Returns notifications by user id
    """
    user = db_session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found!"
        )
    return get_all_notifications_for_user(user=user)
