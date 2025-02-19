from fastapi import APIRouter
from src.app_logic.limit_operations import (
    get_limit,
    get_limits_by_group,
    get_limits_by_user,
    add_limit,
    update_limit,
    remove_limit
)
from src.db.models import Limit
from src.schemas.limit_entities import LimitResponse, LimitRequest
from . import SessionDep

limit_route = APIRouter(
    prefix="/limit"
)


@limit_route.get("/user/{user_id}", response_model=list[LimitResponse])
def get_user_limits(user_id: int, session: SessionDep) -> list[LimitResponse]:
    """
    Returns limits by user id
    """
    return get_limits_by_user(user_id=user_id, session=session)


@limit_route.get("/group/{group_id}", response_model=list[LimitResponse])
def get_group_limits(group_id: int, session: SessionDep) -> list[LimitResponse]:
    """
    Returns limits by group id
    """
    return get_limits_by_group(group_id=group_id, session=session)


@limit_route.get("/{limit_id}", response_model=LimitResponse)
def limit_get(limit_id: int, session: SessionDep) -> LimitResponse:
    """
    Returns limit by id
    """
    return get_limit(limit_id=limit_id, session=session)


@limit_route.post("/", response_model=LimitResponse)
def limit_create(limit: LimitRequest, session: SessionDep) -> LimitResponse:
    """
    Creates new limit
    """
    return add_limit(limit=limit, session=session)


@limit_route.put("/", response_model=LimitResponse)
def limit_update(limit: LimitRequest, session: SessionDep) -> LimitResponse:
    """
    Updates limit
    """
    return update_limit(limit=limit, session=session)


@limit_route.delete("/{limit_id}")
def limit_delete(limit_id: int, session: SessionDep) -> None:
    """
    Deletes limit
    """
    remove_limit(limit_id=limit_id, session=session)
    return {'detail': 'Limit deleted'}