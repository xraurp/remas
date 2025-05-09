from fastapi import APIRouter
from src.app_logic.notification_operations import (
    get_all_notifications,
    get_notification,
    create_notification,
    remove_notification,
    update_notification,
    assign_or_unassign_notification,
    get_notifications_by_group_id,
    get_notifications_by_user_id,
    get_notifications_by_owner
)
from src.schemas.notification_entities import (
    AssignNotificationRequest,
    GroupNotifications
)
from src.db.models import Notification
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

notification_route = APIRouter(
    prefix="/notification"
)


@notification_route.get("", response_model=list[Notification])
def notification_get_all(
    current_user: LoginDep,
    db_session: SessionDep
) -> list[Notification]:
    """
    Returns all notifications.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_notifications(db_session=db_session)


@notification_route.get("/{notification_id}", response_model=Notification)
def notification_get(
    notification_id: int,
    current_user: LoginDep,
    db_session: SessionDep
) -> Notification:
    """
    Returns notification by id.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_notification(
        notification_id=notification_id,
        db_session=db_session
    )

@notification_route.post("", response_model=Notification)
def notification_create(
    notification: Notification,
    current_user: LoginDep,
    db_session: SessionDep
) -> Notification:
    """
    Creates new notification.
    """
    return create_notification(
        notification=notification,
        current_user=current_user,
        db_session=db_session
    )

@notification_route.delete("/{notification_id}", response_model=dict)
def notification_delete(
    notification_id: int,
    current_user: LoginDep,
    db_session: SessionDep
) -> dict:
    """
    Deletes notification by id.
    """
    remove_notification(
        notification_id=notification_id,
        current_user=current_user,
        db_session=db_session
    )
    return {'detail': 'Notification deleted'}

@notification_route.put("", response_model=Notification)
def notification_update(
    notification: Notification,
    current_user: LoginDep,
    db_session: SessionDep
) -> Notification:
    """
    Updates notification.
    """
    return update_notification(
        notification=notification,
        current_user=current_user,
        db_session=db_session
    )

@notification_route.post("/assign", response_model=Notification)
def notification_assign(
    assignment_request: AssignNotificationRequest,
    current_user: LoginDep,
    db_session: SessionDep
) -> Notification:
    """
    Assigns notification to user or group.
    """
    return assign_or_unassign_notification(
        assignment_request=assignment_request,
        current_user=current_user,
        db_session=db_session
    )

@notification_route.post("/unassign", response_model=Notification)
def notification_unassign(
    assignment_request: AssignNotificationRequest,
    current_user: LoginDep,
    db_session: SessionDep
) -> Notification:
    """
    Unassigns notification from user or group.
    """
    return assign_or_unassign_notification(
        assignment_request=assignment_request,
        current_user=current_user,
        db_session=db_session,
        unassign=True
    )

@notification_route.get(
    "/group/{group_id}",
    response_model=list[GroupNotifications]
)
def notification_get_by_group_id(
    group_id: int,
    current_user: LoginDep,
    db_session: SessionDep
) -> list[GroupNotifications]:
    """
    Returns notifications by group id
    """
    return get_notifications_by_group_id(
        group_id=group_id,
        current_user=current_user,
        db_session=db_session
    )

@notification_route.get(
    "/user/{user_id}",
    response_model=list[GroupNotifications]
)
def notification_get_by_user_id(
    user_id: int,
    current_user: LoginDep,
    db_session: SessionDep
) -> list[GroupNotifications]:
    """
    Returns notifications by user id
    """
    return get_notifications_by_user_id(
        user_id=user_id,
        current_user=current_user,
        db_session=db_session
    )

@notification_route.get(
    "/owner/{owner_id}",
    response_model=list[Notification]
)
def notification_get_by_owner(
    owner_id: int,
    current_user: LoginDep,
    db_session: SessionDep
) -> list[GroupNotifications]:
    """
    Returns notifications by owner id
    """
    return get_notifications_by_owner(
        owner_id=owner_id,
        current_user=current_user,
        db_session=db_session
    )
