from src.db.models  import Resource, ResourceAlias
from sqlmodel import select, Session
from src.schemas.resource_entities import AliasRequest

def create_resource(
    resource: Resource,
    db_session: Session
) -> Resource:
    """
    Creates new resource
    """
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)
    return resource

def delete_resource(resource_id: int, db_session: Session) -> None:
    """
    Deletes resource
    """
    resource = db_session.get(Resource, resource_id)
    if not resource:
        raise ValueError(f"Resource with id {resource_id} not found!")
    for alias in resource.aliases:
        if len(alias.resources) == 1:
            db_session.delete(alias)
    db_session.delete(resource)
    db_session.commit()

def get_resource(resource_id: int, db_session: Session) -> Resource:
    """
    Returns resource by id
    """
    return db_session.get(Resource, resource_id)

def get_all_resources(db_session: Session) -> list[Resource]:
    """
    Returns all resources
    """
    return db_session.scalars(select(Resource)).all()

def update_resource(resource: Resource, db_session: Session) -> Resource:
    """
    Updates resource
    """
    db_resource = db_session.get(Resource, resource.id)
    if not db_resource:
        raise ValueError(f"Resource with id {resource.id} not found!")
    db_resource.name = resource.name
    db_resource.description = resource.description
    db_session.commit()
    db_session.refresh(db_resource)
    return db_resource

def add_resource_alias(
    alias_request: AliasRequest,
    db_session: Session
) -> Resource:
    """
    Adds alias to resource
    """
    resource = db_session.get(Resource, alias_request.resource_id)
    if not resource:
        raise ValueError(
            f"Resource with id {alias_request.resource_id} not found!"
        )
    alias = db_session.get(ResourceAlias, alias_request.alias_id)
    if not alias:
        raise ValueError(f"Alias with id {alias_request.alias_id} not found!")
    resource.aliases.append(alias)
    db_session.commit()
    db_session.refresh(resource)
    return resource

def remove_resource_alias(
    alias_request: AliasRequest,
    db_session: Session
) -> Resource:
    """
    Removes alias from resource
    """
    resource = db_session.get(Resource, alias_request.resource_id)
    if not resource:
        raise ValueError(
            f"Resource with id {alias_request.resource_id} not found!"
        )
    alias = db_session.get(ResourceAlias, alias_request.alias_id)
    if not alias:
        raise ValueError(f"Alias with id {alias_request.alias_id} not found!")
    alias.resources.remove(resource)
    db_session.commit()
    db_session.refresh(alias)
    if not len(alias.resources):
        db_session.delete(alias)
        db_session.commit()
    db_session.refresh(resource)
    return resource
