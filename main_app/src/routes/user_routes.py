from fastapi import (
    Depends,
    HTTPException,
    APIRouter
)
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
from src.db.connection import get_db_session
from typing import Annotated
from sqlmodel import Session

user_route = APIRouter(
    prefix="/user"
)

SessionDep = Annotated[Session, Depends(get_db_session)]

@user_route.get("/", response_model=list[UserNoPassword])
def get_users(session: SessionDep) -> list[UserNoPassword]:
    """
    Returns all users.
    """
    return get_all_users(db_session=session)

@user_route.get("/{user_id}", response_model=UserNoPassword)
def user_get(user_id: int, session: SessionDep) -> UserNoPassword:
    """
    Returns user by id.
    """
    return get_user(user_id=user_id, db_session=session)

@user_route.post("/", response_model=UserNoPassword, status_code=201)
def user_create(user: User, session: SessionDep) -> UserNoPassword:
    """
    Creates new user.
    """
    return create_user(user=user, db_session=session)

@user_route.put("/", response_model=UserNoPassword)
def user_update(
    user: UpdateUserRequest,
    session: SessionDep
) -> UserNoPassword:
    """
    Updates user.
    """
    return update_user(user=user, db_session=session)

@user_route.delete("/{user_id}")
def user_delete(user_id: int, session: SessionDep):
    """
    Deletes user.
    """
    try:
        delete_user(user_id=user_id, db_session=session)
        return {'detail': 'User deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
