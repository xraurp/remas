from fastapi import APIRouter
from src.app_logic.resource_operations import (
    get_all_resources,
    get_resource,
    create_resource,
    update_resource,
    delete_resource,
    add_resource_alias,
    remove_resource_alias
)
from src.db.models import Resource
from src.schemas.resource_entities import ResourceResponse, AliasRequest
from . import SessionDep

resource_route = APIRouter(
    prefix="/resource"
)


@resource_route.get("/", response_model=list[ResourceResponse])
def get_resources(session: SessionDep) -> list[ResourceResponse]:
    """
    Returns all resources
    """
    return get_all_resources(db_session=session)

@resource_route.get("/{resource_id}", response_model=ResourceResponse)
def resource_get(resource_id: int, session: SessionDep) -> ResourceResponse:    
    """
    Returns resource by id
    """
    return get_resource(resource_id=resource_id, db_session=session)

@resource_route.post("/", response_model=ResourceResponse)
def resource_create(resource: Resource, session: SessionDep) -> ResourceResponse:
    """
    Creates new resource.
    """
    return create_resource(resource=resource, db_session=session)

@resource_route.put("/", response_model=ResourceResponse)
def resource_update(resource: Resource, session: SessionDep) -> ResourceResponse:
    """
    Updates resource.
    """
    return update_resource(resource=resource, db_session=session)

@resource_route.delete("/{resource_id}", response_model=dict)
def resource_delete(resource_id: int, session: SessionDep) -> dict:
    """
    Deletes resource.
    """
    delete_resource(resource_id=resource_id, db_session=session)
    return {'detail': 'Resource deleted'}

@resource_route.post("/add_alias", response_model=ResourceResponse)
def resource_add_alias(
    request: AliasRequest,
    session: SessionDep
) -> ResourceResponse:
    """
    Adds alias to resource
    """
    return add_resource_alias(alias_request=request, db_session=session)

@resource_route.post("/remove_alias", response_model=ResourceResponse)
def resource_remove_alias(
    request: AliasRequest,
    session: SessionDep
) -> ResourceResponse:
    """
    Removes alias from resource
    """
    return remove_resource_alias(alias_request=request, db_session=session)
