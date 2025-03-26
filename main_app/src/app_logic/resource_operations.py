from src.db.models  import Resource, ResourceAlias
from sqlmodel import select, Session
from src.schemas.resource_entities import AliasRequest
from fastapi import HTTPException
from src.app_logic.grafana_alert_operations import grafana_remove_alert


def create_resource(
    resource: Resource,
    db_session: Session
) -> Resource:
    """
    Creates new resource
    """
    resource.id = None
    resource.nodes = []
    resource.notifications = []

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
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource_id} not found!"
        )
    for alias in resource.aliases:
        if len(alias.resources) == 1:
            db_session.delete(alias)
    # remove Grafana alerts
    for notification in resource.notifications:
        grafana_remove_alert(notification=notification)
    # TODO - remove resource dashboard from Grafana
    db_session.delete(resource)
    db_session.commit()

def get_resource(resource_id: int, db_session: Session) -> Resource:
    """
    Returns resource by id
    """
    resource = db_session.get(Resource, resource_id)
    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource_id} not found!"
        )
    return resource

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
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {resource.id} not found!"
        )
    db_resource.name = resource.name
    db_resource.description = resource.description
    db_session.commit()
    db_session.refresh(db_resource)
    # TODO - update all Grafana alerts for resource
    # TODO - update panels for resource
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
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {alias_request.resource_id} not found!"
        )
    alias = db_session.get(ResourceAlias, alias_request.alias_id)
    if not alias:
        raise HTTPException(
            status_code=404,
            detail=f"Alias with id {alias_request.alias_id} not found!"
        )
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
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {alias_request.resource_id} not found!"
        )
    alias = db_session.get(ResourceAlias, alias_request.alias_id)
    if not alias:
        raise HTTPException(
            status_code=404,
            detail=f"Alias with id {alias_request.alias_id} not found!"
        )
    if alias not in resource.aliases:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {alias_request.resource_id} doesn't have "
                   f"alias with id {alias_request.alias_id}!"
        )
    alias.resources.remove(resource)
    db_session.commit()
    db_session.refresh(alias)
    if not len(alias.resources):
        db_session.delete(alias)
        db_session.commit()
    db_session.refresh(resource)
    return resource
