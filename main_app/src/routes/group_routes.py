from fastapi import APIRouter
from src.app_logic.group_operations import (
    get_all_groups,
    get_group,
    create_group,
    update_group,
    delete_group,
    add_users_to_group,
    change_group_parent
)
from src.db.models import Group
from src.schemas.group_entities import GroupResponse
from . import SessionDep

group_route = APIRouter(
    prefix="/group"
)

@group_route.get("/", response_model=list[GroupResponse])
def get_groups(session: SessionDep) -> list[GroupResponse]:
    """
    Returns all groups.
    """
    return get_all_groups(db_session=session)

@group_route.get("/{group_id}", response_model=GroupResponse)
def group_get(group_id: int, session: SessionDep) -> GroupResponse:
    """
    Returns group by id.
    """
    return get_group(group_id=group_id, db_session=session)

@group_route.post("/", response_model=GroupResponse, status_code=201)
def group_create(group: Group, session: SessionDep) -> GroupResponse:
    """
    Creates new group.
    """
    return create_group(group=group, db_session=session)

@group_route.put("/", response_model=GroupResponse)
def group_update(group: Group, session: SessionDep) -> GroupResponse:
    """
    Updates group.
    """
    return update_group(group=group, db_session=session)

@group_route.delete("/{group_id}")
def group_delete(group_id: int, session: SessionDep) -> dict:
    """
    Deletes group.
    """
    try:
        delete_group(group_id=group_id, db_session=session)
        return {'detail': 'Group deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@group_route.post("/{group_id}", response_model=GroupResponse)
def group_add_users(
    group_id: int,
    user_ids: list[int],
    session: SessionDep
) -> GroupResponse:
    """
    Adds users to group.
    """
    try:
        group = add_users_to_group(
            group_id=group_id,
            user_ids=user_ids,
            db_session=session
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@group_route.post("/{group_id}/parent/{parent_id}", response_model=GroupResponse)
def group_change_parent(
    group_id: int,
    parent_id: int,
    session: SessionDep
) -> GroupResponse:
    """
    Changes group parent.
    """
    try:
        group = change_group_parent(
            group_id=group_id,
            parent_id=parent_id,
            db_session=session
        )
        return group
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
