from fastapi import APIRouter
from src.app_logic.resource_alias_operations import (
    create_resource_alias,
    get_all_resource_aliases,
    get_resource_alias,
    update_resource_alias,
    delete_resource_alias
)
from src.db.models import ResourceAlias
from src.schemas.resource_alias_entities import AliasResponse
from . import SessionDep


resource_alias_route = APIRouter(
    prefix="/resource_alias"
)


@resource_alias_route.get("/", response_model=list[AliasResponse])
def get_resource_aliases(session: SessionDep) -> list[AliasResponse]:
    """
    Returns all resource aliases
    """
    return get_all_resource_aliases(db_session=session)

@resource_alias_route.get("/{alias_id}", response_model=AliasResponse)  
def resource_alias_get(alias_id: int, session: SessionDep) -> AliasResponse:
    """
    Returns resource alias by id
    """
    return get_resource_alias(resource_alias_id=alias_id, db_session=session)

@resource_alias_route.post("/", response_model=AliasResponse)
def resource_alias_create(
    alias: ResourceAlias,
    session: SessionDep
) -> AliasResponse:
    """
    Creates new resource alias
    """
    return create_resource_alias(resource_alias=alias, db_session=session)

@resource_alias_route.put("/", response_model=AliasResponse)
def resource_alias_update(
    alias: ResourceAlias,
    session: SessionDep
) -> AliasResponse:
    """
    Updates resource alias
    """
    return update_resource_alias(resource_alias=alias, db_session=session)

@resource_alias_route.delete("/{alias_id}")
def resource_alias_delete(alias_id: int, session: SessionDep) -> None:
    """
    Deletes resource alias
    """
    delete_resource_alias(resource_alias_id=alias_id, db_session=session)
    return {'detail': 'Resource alias deleted'}
