from src.db.models import Group, User
from src.schemas.group_entities import (
    UserGroupChangeRequest,
    GroupChangeParentRequest
)
from src.schemas.authentication_entities import CurrentUserInfo
from src.app_logic.authentication import insufficientPermissionsException
from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.app_logic.grafana_user_operations import grafana_create_or_update_user
from src.app_logic.grafana_alert_operations import get_alert_error
from src.app_logic.auxiliary_operations import (
    get_members_including_subgroups
)

def create_group(
    group: Group,
    db_session: Session
) -> Group:
    """
    Creates new group.
    """
    group.id = None
    # must be assigned explicitly
    group.members = []
    group.notifications = []

    if group.name == 'None':
        raise HTTPException(
            status_code=400,
            detail="'None' is reserved keyword that cannot "
                   "be used as group name!"
        )

    try:
        db_session.add(group)
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create group in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(group)
    return group

def get_group(
    group_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> Group:
    """
    Returns group by id.
    """
    # check if user is admin or member of the group
    if not current_user.is_admin:
        user = db_session.get(User, current_user.id)
        if not user.group_id == group_id:
            raise insufficientPermissionsException
    
    return db_session.get(Group, group_id)

def get_all_groups(db_session: Session) -> list[Group]:
    """
    Returns all groups.
    """
    return db_session.scalars(select(Group)).all()

def update_group(group: Group, db_session: Session) -> Group:
    """
    Updates group.
    """
    db_group = db_session.get(Group, group.id)
    if not db_group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group.id} not found!"
        )
    if group.name == 'None':
        raise HTTPException(
            status_code=400,
            detail="'None' is reserved keyword that cannot "
                   "be used as group name!"
        )
    db_group.name = group.name
    db_group.description = group.description
    db_group.users_share_statistics = group.users_share_statistics
    try:
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to update group in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(db_group)
    return db_group

def delete_group(group_id: int, db_session: Session) -> None:
    """
    Deletes group.
    """
    if group_id <= 3:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete default groups!"
        )
    db_group = db_session.get(Group, group_id)
    if not db_group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group_id} not found!"
        )
    users = get_members_including_subgroups(group=db_group)
    gid = 3  # User group
    if db_group.parent_id:
        gid = db_group.parent_id
    for user in db_group.members:
        user.group_id = gid
    db_session.commit()
    db_session.delete(db_group)
    db_session.commit()
    # update Grafana alerts for users and subgroups
    for user in users:
        grafana_create_or_update_user(user=user, db_session=db_session)

def add_user_to_group(
    request: UserGroupChangeRequest,
    db_session: Session
) -> Group:
    """
    Adds user to group.
    """
    group = db_session.get(Group, request.group_id)
    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {request.group_id} not found!"
        )
    user = db_session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {request.user_id} not found!"
        )
    group.members.append(user)
    db_session.commit()
    db_session.refresh(group)
    # update user in Grafana
    grafana_create_or_update_user(user=user, db_session=db_session)
    return group

def change_group_parent(
    request: GroupChangeParentRequest,
    db_session: Session
) -> Group:
    """
    Changes group parent.
    """
    if request.group_id == request.parent_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot change group parent to itself!"
        )
    group = db_session.get(Group, request.group_id)
    parent = db_session.get(Group, request.parent_id)
    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {request.group_id} not found!"
        )
    if not parent:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {request.parent_id} not found!"
        )
    if group.id <= 3:
        raise HTTPException(
            status_code=403,
            detail="Cannot change default groups!"
        )
    group.parent_id = request.parent_id
    db_session.commit()
    db_session.refresh(group)
    # update Grafana alerts for users and subgroups
    users = get_members_including_subgroups(group=group)
    for user in users:
        grafana_create_or_update_user(
            user=user,
            db_session=db_session
        )
    return group
