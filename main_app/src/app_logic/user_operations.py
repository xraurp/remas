from src.db.models import User
from src.schemas.user_entities import UpdateUserRequest
from sqlmodel import select, Session

# TODO - query notifications when receiving user

def create_user(
    user: User,
    db_session: Session
) -> User:
    """
    Creates new user.
    """
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def get_user(user_id: int, db_session: Session) -> User:
    """
    Returns user by id.
    """
    return db_session.get(User, user_id)

def get_all_users(db_session: Session) -> list[User]:
    """
    Returns all users.
    """
    result = db_session.scalars(select(User)).all()
    return result

def update_user(user: UpdateUserRequest, db_session: Session) -> User:
    """
    Updates user.
    """
    db_user = db_session.get(User, user.id)
    if not db_user:
        raise ValueError(f"User with id {user.id} not found!")
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
        raise ValueError("Cannot delete default user!")
    db_user = db_session.get(User, user_id)
    if not db_user:
        raise ValueError(f"User with id {user_id} not found!")
    db_session.delete(db_user)
    db_session.commit()
