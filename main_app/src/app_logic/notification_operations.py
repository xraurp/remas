from src.db.models import (
    Notification,
    User,
    Group,
    NotificationType,
    Event,
    EventType,
    Task,
    TaskStatus
)
from sqlmodel import select, Session
from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound, IntegrityError
from src.schemas.notification_entities import (
    AssignNotificationRequest,
    GroupNotifications
)
from src.schemas.authentication_entities import CurrentUserInfo
from src.app_logic.authentication import insufficientPermissionsException
from datetime import datetime, timedelta
from src.app_logic.auxiliary_operations import (
    get_all_notifications_for_user,
    get_all_notifications_for_group
)
from src.app_logic.grafana_alert_operations import (
    grafana_remove_alert_from_user,
    grafana_remove_alert,
    update_grafana_alert_for_all_users_and_groups,
    grafana_remove_alert_for_group,
    grafana_add_alert_to_user,
    grafana_add_alert_to_group
)

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
    current_user: CurrentUserInfo,
    db_session: Session
) -> Notification:
    """
    Creates new notification
    """
    notification.id = None
    notification.receivers_groups = []
    notification.receivers_users = []
    try:
        notification.type = NotificationType(notification.type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid notification type {notification.type}!"
        )
    if is_scheduleble_notification(notification):
        if not notification.time_offset:
            notification.time_offset = 0
    elif is_grafana_alert(notification):
        if not notification.default_amount:
            raise HTTPException(
                status_code=400,
                detail="Default amount is required for grafana alerts!"
            )
        if not notification.resource_id:
            raise HTTPException(
                status_code=400,
                detail="Resource must be set for grafana alerts!"
            )
        if not notification.notification_template:
            raise HTTPException(
                status_code=400,
                detail="Notification template must be set for grafana alerts!"
            )
    if current_user.is_admin:
        notification.owner_id = None
    else:
        notification.owner_id = current_user.user_id
    try:
        db_session.add(notification)
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create notification in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(notification)
    return notification

def remove_notification(
    notification_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> None:
    """
    Removes notification
    """
    notification = db_session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {notification_id} not found!"
        )
    if notification.owner_id != current_user.user_id \
    and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail=f"Can't remove notification owned by another user!"
        )
    
    # check if notification is grafana alert and remove it from grafana
    if is_grafana_alert(notification):
        grafana_remove_alert(notification=notification)

    db_session.delete(notification)
    db_session.commit()

def is_grafana_alert(notification: Notification) -> bool:
    return notification.type in (
        NotificationType.grafana_resource_exceedance_task,
        NotificationType.grafana_resource_exceedance_general
    )

def is_scheduleble_notification(notification: Notification) -> bool:
    return notification.type in (
        NotificationType.task_start,
        NotificationType.task_end
    )

def update_notification(
    notification: Notification,
    current_user: CurrentUserInfo,
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
    if db_notification.owner_id != current_user.user_id \
    and not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail=f"Can't update notification owned by another user!"
        )
    
    # Fix notification type
    notification.type = NotificationType(notification.type)
    
    # check if notification needs to be rescheduled
    reschedule = False
    remove_scheudling = False
    if is_scheduleble_notification(db_notification) \
    and not is_scheduleble_notification(notification):
        remove_scheudling = True
    elif notification.type != db_notification.type \
    or notification.time_offset != db_notification.time_offset:
        reschedule = True

    # check if notification resource is changed
    remove_old_notification = False
    if db_notification.resource_id != notification.resource_id:
        remove_old_notification = True
        grafana_remove_alert(notification=db_notification)

    # update notification
    db_notification.name = notification.name
    db_notification.description = notification.description
    db_notification.type = notification.type
    db_notification.notification_template = notification.notification_template
    try:
        if not is_grafana_alert(db_notification):
            # update schedulebe notification
            db_notification.time_offset = notification.time_offset
        else:
            # update grafana alert
            db_notification.default_amount = notification.default_amount
            db_notification.resource_id = notification.resource_id
            if not db_notification.default_amount:
                raise HTTPException(
                    status_code=400,
                    detail="Default amount is required for grafana alerts!"
                )
            if not db_notification.resource_id:
                raise HTTPException(
                    status_code=400,
                    detail="Resource must be set for grafana alerts!"
                )
            if not db_notification.notification_template:
                raise HTTPException(
                    status_code=400,
                    detail="Notification template must be set for grafana "
                           "alerts!"
                )
        db_session.commit()
    except Exception as e:
        if remove_old_notification:
            # rollback changes
            db_session.rollback()
            db_session.refresh(db_notification)
            update_grafana_alert_for_all_users_and_groups(
                notification=db_notification,
                db_session=db_session
            )
        if isinstance(e, IntegrityError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Failed to update notification in database due to conflict:"
                       f"\n{e.orig.pgerror}"
            )
        raise e
    db_session.refresh(db_notification)
    # check if notification is grafana alert and update it in grafana
    if is_grafana_alert(db_notification):
        update_grafana_alert_for_all_users_and_groups(
            notification=db_notification,
            db_session=db_session
        )
    # reschedule notification after update
    if remove_scheudling:
        remove_notification_scheduling_for_all(
            notification=db_notification,
            db_session=db_session
        )
        db_session.commit()
        db_session.refresh(db_notification)
    elif reschedule:
        reschedule_notification_events_for_all(
            notification=db_notification,
            db_session=db_session
        )
        db_session.commit()
        db_session.refresh(db_notification)
    return db_notification

def assign_or_unassign_notification(
    assignment_request: AssignNotificationRequest,
    current_user: CurrentUserInfo,
    db_session: Session,
    unassign: bool = False
) -> Notification:
    """
    Assigns / unassignes notification to/from user or group in the request.
    :param assignment_request (AssignNotificationRequest): request with id of
        group or user to which notification will be assigned / removed from
    :param current_user (CurrentUserInfo): current user
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
        assignment_request.notification_id
    )
    if not db_notification:
        raise HTTPException(
            status_code=404,
            detail=f"Notification with id {assignment_request.notification_id}"
                    " not found!"
        )
    
    if not current_user.is_admin:
        if assignment_request.group_id:
            raise HTTPException(
                status_code=403,
                detail="Can't assign/unassign notification to/from group! "
                       "Insufficient permissions!"
            )
        if assignment_request.user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can't assign/unassign notification to/from another "
                       "user!"
            )
        if db_notification.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Can't assign/unassign notification owned by another "
                       "user!"
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
    
    if unassign:  # remove notification assignment
        if user and user in db_notification.receivers_users:
            if is_grafana_alert(db_notification):
                grafana_remove_alert_from_user(
                    user=user,
                    notification=db_notification,
                    db_session=db_session
                )
            db_notification.receivers_users.remove(user)
            db_session.commit()
            remove_notification_scheduling_for_user(
                notification=db_notification,
                user=user,
                db_session=db_session
            )
        if group and group in db_notification.receivers_groups:
            if is_grafana_alert(db_notification):
                grafana_remove_alert_for_group(
                    group=group,
                    notification=db_notification,
                    db_session=db_session
                )
            db_notification.receivers_groups.remove(group)
            db_session.commit()
            remove_notification_scheduling_for_group(
                notification=db_notification,
                group=group,
                db_session=db_session
            )
    else:  # assign notification
        if user and user not in db_notification.receivers_users:
            db_notification.receivers_users.append(user)
            db_session.commit()
            schedule_notification_events_for_user(
                notification=db_notification,
                user=user,
                db_session=db_session
            )
            if is_grafana_alert(db_notification):
                grafana_add_alert_to_user(
                    user=user,
                    notification=db_notification,
                    db_session=db_session
                )
        if group and group not in db_notification.receivers_groups:
            db_notification.receivers_groups.append(group)
            db_session.commit()
            schedule_notification_events_for_group(
                notification=db_notification,
                group=group,
                db_session=db_session
            )
            if is_grafana_alert(db_notification):
                grafana_add_alert_to_group(
                    group=group,
                    notification=db_notification,
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
    Commit changes in database.
    """
    # check if notification needs to be scheduled
    if not is_scheduleble_notification(notification):
        return

    # check if notification is scheduled already
    scheduled_event = None
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
    else:
        # do not schedule notification for end time
        # if task is has already finished
        if task.status == TaskStatus.finished:
            return
        start = task.end_time + timedelta(seconds=notification.time_offset)
    
    # schedule the notification
    if scheduled_event:
        # reschedule existing
        if scheduled_event.time != start:
            scheduled_event.time = start
    else:
        # schedule new
        scheduled_event = Event(
            id = None,
            name = f"Task: {task.name}, notification: {notification.name}",
            time = start,
            type = EventType.other,
            task_id = task.id,
            notification_id = notification.id
        )
        db_session.add(scheduled_event)
    db_session.commit()

def schedule_notification_events_for_user(
    notification: Notification,
    user: User,
    db_session: Session
) -> Notification:
    """
    Schedule notification events for user.
    """
    # check if notification needs to be scheduled
    if not is_scheduleble_notification(notification):
        return

    for task in user.tasks:
        schedule_notification_events_for_task(
            notification=notification,
            task=task,
            db_session=db_session
        )

def schedule_notification_events_for_group(
    notification: Notification,
    group: Group,
    db_session: Session
) -> None:
    """
    Schedule notification events for group.
    """
    # check if notification needs to be scheduled
    if not is_scheduleble_notification(notification):
        return
    
    for user in group.members:
        schedule_notification_events_for_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
    
    for subgroup in group.children:
        schedule_notification_events_for_group(
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
    """
    # check if notification needs to be scheduled
    if not is_scheduleble_notification(notification):
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

def get_notifications_by_group_id(
    group_id: int,
    current_user: CurrentUserInfo,
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
    if not current_user.is_admin:
        user = db_session.get(User, current_user.user_id)
        if not user.group_id == group_id:
            raise insufficientPermissionsException
    return get_all_notifications_for_group(group=group)

def get_notifications_by_user_id(
    user_id: int,
    current_user: CurrentUserInfo,
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
    if not current_user.is_admin:
        if not current_user.user_id == user_id:
            raise insufficientPermissionsException
    return get_all_notifications_for_user(user=user)
