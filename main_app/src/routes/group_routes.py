from fastapi import APIRouter
from src.app_logic.group_operations import (
    get_all_groups,
    get_group,
    create_group,
    update_group,
    delete_group,
    add_user_to_group,
    change_group_parent
)
from src.db.models import Group
from src.schemas.group_entities import (
    GroupResponse,
    UserGroupChangeRequest,
    GroupChangeParentRequest
)
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

group_route = APIRouter(
    prefix="/group"
)

@group_route.get("", response_model=list[GroupResponse])
def get_groups(
    session: SessionDep,
    current_user: LoginDep
) -> list[GroupResponse]:
    """
    Returns all groups.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_groups(db_session=session)

@group_route.get("/{group_id}", response_model=GroupResponse)
def group_get(
    group_id: int,
    session: SessionDep,
    current_user: LoginDep
) -> GroupResponse:
    """
    Returns group by id.
    """
    return get_group(
        group_id=group_id,
        current_user=current_user,
        db_session=session
    )

@group_route.post("", response_model=GroupResponse, status_code=201)
def group_create(
    group: Group,
    current_user: LoginDep,
    session: SessionDep
) -> GroupResponse:
    """
    Creates new group.
    """
    ensure_admin_permissions(current_user=current_user)
    return create_group(group=group, db_session=session)

@group_route.put("", response_model=GroupResponse)
def group_update(
    group: Group,
    current_user: LoginDep,
    session: SessionDep
) -> GroupResponse:
    """
    Updates group.
    """
    ensure_admin_permissions(current_user=current_user)
    return update_group(group=group, db_session=session)

@group_route.delete("/{group_id}")
def group_delete(
    group_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> dict:
    """
    Deletes group.
    """
    ensure_admin_permissions(current_user=current_user)
    delete_group(group_id=group_id, db_session=session)
    return {'detail': 'Group deleted'}

@group_route.post("/add-user", response_model=GroupResponse)
def group_add_user(
    request: UserGroupChangeRequest,
    current_user: LoginDep,
    session: SessionDep
) -> GroupResponse:
    """
    Adds users to group.
    """
    ensure_admin_permissions(current_user=current_user)
    return add_user_to_group(
        request=request,
        db_session=session
    )

@group_route.post("/change-parent", response_model=GroupResponse)
def group_change_parent(
    request: GroupChangeParentRequest,
    current_user: LoginDep,
    session: SessionDep
) -> GroupResponse:
    """
    Changes group parent.
    """
    ensure_admin_permissions(current_user=current_user)
    return change_group_parent(
        request=request,
        db_session=session
    )
