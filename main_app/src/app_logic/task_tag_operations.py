from src.db.models import TaskTag, User, Group
from sqlmodel import select, Session
from fastapi import HTTPException
from src.app_logic.authentication import insufficientPermissionsException
from src.schemas.authentication_entities import CurrentUserInfo


def create_tag(
    tag: TaskTag,
    current_user: CurrentUserInfo,
    db_session: Session
) -> TaskTag:
    """
    Creates tag
    """
    tag.id = None
    tag.user_id = current_user.user_id
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    return tag


def delete_tag(
    tag_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> None:
    """
    Deletes tag
    """
    tag = db_session.get(TaskTag, tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag_id} not found!"
        )
    if not current_user.is_admin and tag.user_id != current_user.user_id:
        raise insufficientPermissionsException
    db_session.delete(tag)
    db_session.commit()

def update_tag(
    tag: TaskTag,
    current_user: CurrentUserInfo,
    db_session: Session
) -> TaskTag:
    """
    Updates tag
    """
    db_tag = db_session.get(TaskTag, tag.id)
    if not db_tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag.id} not found!"
        )
    if not current_user.is_admin and tag.user_id != current_user.user_id:
        raise insufficientPermissionsException
    db_tag.name = tag.name
    db_tag.description = tag.description
    db_session.commit()
    db_session.refresh(db_tag)
    return db_tag

def get_tag(
    tag_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> TaskTag:
    """
    Returns tag
    """
    tag = db_session.get(TaskTag, tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag_id} not found!"
        )
    if not current_user.is_admin and tag.user_id != current_user.user_id:
        raise insufficientPermissionsException
    return tag


def get_user_tags(
    user_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> list[TaskTag]:
    """
    Returns user tags
    """
    if not current_user.is_admin and current_user.user_id != user_id:
        raise insufficientPermissionsException
    return db_session.exec(
        select(TaskTag).where(TaskTag.user_id == user_id)
    ).all()

def get_all_tags(
    db_session: Session
) -> list[TaskTag]:
    """
    Returns user tags
    """
    return db_session.exec(select(TaskTag)).all()

def get_group_tags(
    group_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> list[TaskTag]:
    """
    Returns group tags
    """
    if not current_user.is_admin:
        user = db_session.get(User, current_user.user_id)
        if user.group_id != group_id:
            raise insufficientPermissionsException
        if not user.group.users_share_statistics:
            raise insufficientPermissionsException
    group = db_session.get(Group, group_id)
    if not group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group_id} not found!"
        )
    return db_session.exec(
        select(TaskTag).where(TaskTag.user_id.in_(
            [user.id for user in group.members]
        ))
    ).all()
