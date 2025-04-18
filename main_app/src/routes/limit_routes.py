from fastapi import APIRouter
from src.app_logic.limit_operations import (
    get_limit,
    get_limits_by_group,
    get_limits_by_user,
    add_limit,
    update_limit,
    remove_limit,
    get_all_user_limits_list,
    get_all_group_limits_list,
    get_all_limits
)
from src.db.models import Limit
from src.schemas.limit_entities import LimitResponse, LimitRequest
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

limit_route = APIRouter(
    prefix="/limit"
)


@limit_route.get("/user/{user_id}", response_model=list[LimitResponse])
def get_user_limits(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[LimitResponse]:
    """
    Returns limits by user id
    """
    ensure_admin_permissions(current_user=current_user)
    return get_limits_by_user(user_id=user_id, session=session)


@limit_route.get("/group/{group_id}", response_model=list[LimitResponse])
def get_group_limits(
    group_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[LimitResponse]:
    """
    Returns limits by group id
    """
    ensure_admin_permissions(current_user=current_user)
    return get_limits_by_group(group_id=group_id, session=session)

@limit_route.get("/group_all/{group_id}", response_model=list[LimitResponse])
def get_group_limits_all(
    group_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[LimitResponse]:
    """
    Returns all limits by group id (including all subgroup limits)
    """
    return get_all_group_limits_list(
        group_id=group_id,
        current_user=current_user,
        session=session
    )

@limit_route.get("/user_all/{user_id}", response_model=list[LimitResponse])
def get_user_limits_all(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[LimitResponse]:
    """
    Returns all limits by user id (including all group and subgroup limits)
    """
    return get_all_user_limits_list(
        user_id=user_id,
        current_user=current_user,
        session=session
    )

@limit_route.get("/{limit_id}", response_model=LimitResponse)
def limit_get(
    limit_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> LimitResponse:
    """
    Returns limit by id
    """
    ensure_admin_permissions(current_user=current_user)
    return get_limit(limit_id=limit_id, session=session)

@limit_route.get("", response_model=list[LimitResponse])
def limit_get_all(
    current_user: LoginDep,
    session: SessionDep
) -> list[LimitResponse]:
    """
    Returns all limits
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_limits(session=session)

@limit_route.post("", response_model=LimitResponse)
def limit_create(
    limit: LimitRequest,
    current_user: LoginDep,
    session: SessionDep
) -> LimitResponse:
    """
    Creates new limit
    """
    ensure_admin_permissions(current_user=current_user)
    return add_limit(limit=limit, session=session)


@limit_route.put("", response_model=LimitResponse)
def limit_update(
    limit: LimitRequest,
    current_user: LoginDep,
    session: SessionDep
) -> LimitResponse:
    """
    Updates limit
    """
    ensure_admin_permissions(current_user=current_user)
    return update_limit(limit=limit, session=session)


@limit_route.delete("/{limit_id}")
def limit_delete(
    limit_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> None:
    """
    Deletes limit
    """
    ensure_admin_permissions(current_user=current_user)
    remove_limit(limit_id=limit_id, session=session)
    return {'detail': 'Limit deleted'}
