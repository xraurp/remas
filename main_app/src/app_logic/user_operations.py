from src.db.models import User, Group
from src.app_logic.authentication import get_password_hash
from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.app_logic.authentication import insufficientPermissionsException
from src.schemas.authentication_entities import CurrentUserInfo
from src.schemas.user_entities import UserNoPasswordSimple
from src.app_logic.grafana_user_operations import (
    grafana_create_or_update_user,
    grafana_remove_user
)

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
    password = user.password
    user.password = get_password_hash(user.password)
    try:
        db_session.add(user)
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create user in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(user)
    # init user in Grafana (including password)
    grafana_create_or_update_user(
        user=user,
        db_session=db_session,
        password=password
    )
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
    user: UserNoPasswordSimple,
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

    if user.uid != db_user.uid:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can change uid!"
            )
        db_user.uid = user.uid

    try:
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to update user in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(db_user)
    # update user in Grafana
    grafana_create_or_update_user(user=db_user, db_session=db_session)
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
    grafana_remove_user(user=db_user)
    db_session.delete(db_user)
    db_session.commit()
