from src.db.models import TaskTag
from sqlmodel import select, Session
from fastapi import HTTPException


def create_tag(tag: TaskTag, user_id: int, db_session: Session) -> TaskTag:
    """
    Creates tag
    """
    tag.id = None
    tag.user_id = user_id
    db_session.add(tag)
    db_session.commit()
    db_session.refresh(tag)
    return tag


def delete_tag(tag_id: int, user_id: int, db_session: Session) -> None:
    """
    Deletes tag
    """
    tag = db_session.get(TaskTag, tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag_id} not found!"
        )
    if tag.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't delete tag owned by another user!"
        )
    db_session.delete(tag)
    db_session.commit()

def update_tag(tag: TaskTag, user_id: int, db_session: Session) -> TaskTag:
    """
    Updates tag
    """
    db_tag = db_session.get(TaskTag, tag.id)
    if not db_tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag.id} not found!"
        )
    if db_tag.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't update tag owned by another user!"
        )
    db_tag.name = tag.name
    db_tag.description = tag.description
    db_session.commit()
    db_session.refresh(db_tag)
    return db_tag

def get_tag(tag_id: int, user_id: int, db_session: Session) -> TaskTag:
    """
    Returns tag
    """
    tag = db_session.get(TaskTag, tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {tag_id} not found!"
        )
    if tag.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't get tag owned by another user!"
        )
    return tag


def get_user_tags(user_id: int, db_session: Session) -> list[TaskTag]:
    """
    Returns user tags
    """
    return db_session.exec(
        select(TaskTag).where(TaskTag.user_id == user_id)
    ).all()
