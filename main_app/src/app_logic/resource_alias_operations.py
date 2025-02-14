from src.db.models import ResourceAlias
from sqlmodel import select, Session

def create_resource_alias(
    resource_alias: ResourceAlias,
    db_session: Session
) -> ResourceAlias:
    """
    Creates new resource alias
    """
    db_session.add(resource_alias)
    db_session.commit()
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
    return db_session.scalars(
        select(ResourceAlias).where(ResourceAlias.id == resource_alias_id)
    ).one()

def update_resource_alias(
    resource_alias: ResourceAlias,
    db_session: Session
) -> ResourceAlias:
    """
    Updates resource alias
    """
    db_resource_alias = db_session.get(ResourceAlias, resource_alias.id)
    if not db_resource_alias:
        raise ValueError(f"Resource alias with id {resource_alias.id} not found!")
    db_resource_alias.name = resource_alias.name
    db_resource_alias.description = resource_alias.description
    db_session.commit()
    db_session.refresh(db_resource_alias)
    return db_resource_alias

def delete_resource_alias(
    resource_alias_id: int,
    db_session: Session
) -> None:
    """
    Deletes resource alias by id
    """
    db_session.delete(db_session.get(ResourceAlias, resource_alias_id))
    db_session.commit()
