from src.db.models import ResourceAlias
from sqlmodel import select, Session
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

def create_resource_alias(
    resource_alias: ResourceAlias,
    db_session: Session
) -> ResourceAlias:
    """
    Creates new resource alias
    """
    resource_alias.id = None
    try:
        db_session.add(resource_alias)
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create resource alias in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(resource_alias)
    return resource_alias

def get_all_resource_aliases(db_session: Session) -> list[ResourceAlias]:
    """
    Returns all resource aliases
    """
    return db_session.scalars(select(ResourceAlias)).all()

def get_resource_alias(
    resource_alias_id: int,
    db_session: Session
) -> ResourceAlias:
    """
    Returns resource alias by id
    """
    alias = db_session.get(ResourceAlias, resource_alias_id)
    if not alias:
        raise HTTPException(
            status_code=404,
            detail=f"Resource alias with id {resource_alias_id} not found!"
        )
    return alias

def update_resource_alias(
    resource_alias: ResourceAlias,
    db_session: Session
) -> ResourceAlias:
    """
    Updates resource alias
    """
    db_resource_alias = db_session.get(ResourceAlias, resource_alias.id)
    if not db_resource_alias:
        raise HTTPException(
            status_code=404,
            detail=f"Resource alias with id {resource_alias.id} not found!"
        )
    db_resource_alias.name = resource_alias.name
    db_resource_alias.description = resource_alias.description
    try:
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to update resource alias in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(db_resource_alias)
    return db_resource_alias

def delete_resource_alias(
    resource_alias_id: int,
    db_session: Session
) -> None:
    """
    Deletes resource alias by id
    """
    alias = db_session.get(ResourceAlias, resource_alias_id)
    if not alias:
        raise HTTPException(
            status_code=404,
            detail=f"Resource alias with id {resource_alias_id} not found!"
        )
    db_session.delete(alias)
    db_session.commit()
