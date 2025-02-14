from fastapi import APIRouter
from src.app_logic.resource_operations import (
    get_all_resources,
    get_resource,
    create_resource,
    update_resource,
    delete_resource
)
from src.db.models import Resource
from src.schemas.resource_entities import ResourceResponse
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

@resource_route.delete("/{resource_id}")
def resource_delete(resource_id: int, session: SessionDep):
    """
    Deletes resource.
    """
    try:
        delete_resource(resource_id=resource_id, db_session=session)
        return {'detail': 'Resource deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
