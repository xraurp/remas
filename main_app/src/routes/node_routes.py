from fastapi import APIRouter
from src.app_logic.node_operations import (
    get_all_nodes,
    get_node,
    create_node,
    update_node,
    delete_node,
    add_resource_to_node,
    remove_resource_from_node
)
from src.db.models import Node
from src.schemas.node_entities import NodeResponse, NodeProvidesResourceRequest
from . import SessionDep

node_route = APIRouter(
    prefix="/node"
)

@node_route.get("/", response_model=list[NodeResponse])
def get_nodes(session: SessionDep) -> list[NodeResponse]:
    """
    Returns all nodes.
    """
    return get_all_nodes(db_session=session)

@node_route.get("/{node_id}", response_model=NodeResponse)
def node_get(node_id: int, session: SessionDep) -> NodeResponse:
    """
    Returns node by id.
    """
    return get_node(node_id=node_id, db_session=session)

@node_route.post("/", response_model=NodeResponse)
def node_create(node: Node, session: SessionDep) -> NodeResponse:
    """
    Creates new node.
    """
    return create_node(node=node, db_session=session)

@node_route.put("/", response_model=NodeResponse)
def node_update(node: Node, session: SessionDep) -> NodeResponse:
    """
    Updates node.
    """
    return update_node(node=node, db_session=session)

@node_route.delete("/{node_id}", response_model=dict)
def node_delete(node_id: int, session: SessionDep):
    """
    Deletes node.
    """
    try:
        delete_node(node_id=node_id, db_session=session)
        return {'detail': 'Node deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@node_route.post("/add_resource", response_model=NodeResponse)
def node_add_resource(
    resource_request: NodeProvidesResourceRequest,
    session: SessionDep
) -> NodeResponse:
    """
    Adds resource to node.
    """
    try:
        node = add_resource_to_node(
            request=resource_request,
            db_session=session
        )
        return node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@node_route.post("/remove_resource", response_model=NodeResponse)
def node_remove_resource(
    resource_request: NodeProvidesResourceRequest,
    session: SessionDep
) -> NodeResponse:
    """
    Removes resource from node.
    """
    try:
        node = remove_resource_from_node(
            request=resource_request,
            db_session=session
        )
        return node
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
