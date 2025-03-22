from fastapi import APIRouter
from src.app_logic.user_operations import (
    get_all_users,
    get_user,
    create_user,
    update_user,
    delete_user
)
from src.db.models import User
from src.schemas.user_entities import (
    UpdateUserRequest,
    UserNoPassword
)
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

user_route = APIRouter(
    prefix="/user"
)

@user_route.get("", response_model=list[UserNoPassword])
def get_users(
    current_user: LoginDep,
    session: SessionDep
) -> list[UserNoPassword]:
    """
    Returns all users.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_users(db_session=session)

@user_route.get("/{user_id}", response_model=UserNoPassword)
def user_get(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> UserNoPassword:
    """
    Returns user by id.
    """
    return get_user(
        user_id=user_id,
        current_user=current_user,
        db_session=session
    )

@user_route.post("", response_model=UserNoPassword, status_code=201)
def user_create(
    user: User,
    current_user: LoginDep,
    session: SessionDep
) -> UserNoPassword:
    """
    Creates new user.
    """
    ensure_admin_permissions(current_user=current_user)
    return create_user(user=user, db_session=session)

@user_route.put("", response_model=UserNoPassword)
def user_update(
    user: UpdateUserRequest,
    current_user: LoginDep,
    session: SessionDep
) -> UserNoPassword:
    """
    Updates user.
    """
    return update_user(
        user=user,
        current_user=current_user,
        db_session=session
    )

@user_route.delete("/{user_id}", response_model=dict)
def user_delete(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> dict:
    """
    Deletes user.
    """
    ensure_admin_permissions(current_user=current_user)
    delete_user(user_id=user_id, db_session=session)
    return {'detail': 'User deleted'}
