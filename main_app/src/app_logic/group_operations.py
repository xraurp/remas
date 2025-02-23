from src.db.models import Group, User
from src.schemas.group_entities import (
    UserGroupChangeRequest,
    GroupChangeParentRequest
)
from src.schemas.authentication_entities import CurrentUserInfo
from src.app_logic.authentication import insufficientPermissionsException
from sqlmodel import select, Session
from fastapi import HTTPException

# TODO - query notifications when receiving group

def create_group(
    group: Group,
    db_session: Session
) -> Group:
    """
    Creates new group.
    """
    group.id = None
    db_session.add(group)
    db_session.commit()
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
    db_group.name = group.name
    db_group.description = group.description
    db_group.users_share_statistics = group.users_share_statistics
    db_session.commit()
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
    gid = 3  # User group
    if db_group.parent_id:
        gid = db_group.parent_id
    for user in db_group.members:
        user.group_id = gid
    db_session.commit()
    db_session.delete(db_group)
    db_session.commit()

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
    return group
