from src.db.models import User, Group
from src.schemas.user_entities import UpdateUserRequest
from src.app_logic.authentication import get_password_hash
from sqlmodel import select, Session
from fastapi import HTTPException
from src.app_logic.authentication import insufficientPermissionsException
from src.schemas.authentication_entities import CurrentUserInfo

# TODO - query notifications when receiving user

def create_user(
    user: User,
    db_session: Session
) -> User:
    """
    Creates new user.
    """
    user.id = None
    if user.group_id:
        group = db_session.get(Group, user.group_id)
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Group with id {user.group_id} not found!"
            )
    user.password = get_password_hash(user.password)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def get_user(
    user_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> User:
    """
    Returns user by id.
    """
    if not current_user.is_admin:
        if not current_user.user_id == user_id:
            raise insufficientPermissionsException
    
    user = db_session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found!"
        )
    return user

def get_all_users(db_session: Session) -> list[User]:
    """
    Returns all users.
    """
    return db_session.scalars(select(User)).all()

def update_user(
    user: UpdateUserRequest,
    current_user: CurrentUserInfo,
    db_session: Session
) -> User:
    """
    Updates user.
    """
    if not current_user.is_admin:
        if not current_user.user_id == user.id:
            raise insufficientPermissionsException
    
    db_user = db_session.get(User, user.id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user.id} not found!"
        )
    db_user.name = user.name
    db_user.surname = user.surname
    db_user.email = user.email
    db_session.commit()
    db_session.refresh(db_user)
    return db_user

def delete_user(user_id: int, db_session: Session) -> None:
    """
    Deletes user.
    """
    if user_id == 1:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete default user!"
        )
    db_user = db_session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found!"
        )
    db_session.delete(db_user)
    db_session.commit()
