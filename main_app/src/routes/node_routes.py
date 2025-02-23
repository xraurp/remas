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
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

node_route = APIRouter(
    prefix="/node"
)

@node_route.get("/", response_model=list[NodeResponse])
def get_nodes(
    current_user: LoginDep,  # ensure user is logged in
    session: SessionDep
) -> list[NodeResponse]:
    """
    Returns all nodes.
    """
    return get_all_nodes(db_session=session)

@node_route.get("/{node_id}", response_model=NodeResponse)
def node_get(
    node_id: int,
    current_user: LoginDep,  # ensure user is logged in
    session: SessionDep
) -> NodeResponse:
    """
    Returns node by id.
    """
    return get_node(node_id=node_id, db_session=session)

@node_route.post("/", response_model=NodeResponse)
def node_create(
    node: Node,
    current_user: LoginDep,
    session: SessionDep
) -> NodeResponse:
    """
    Creates new node.
    """
    ensure_admin_permissions(current_user=current_user)
    return create_node(node=node, db_session=session)

@node_route.put("/", response_model=NodeResponse)
def node_update(
    node: Node,
    current_user: LoginDep,
    session: SessionDep
) -> NodeResponse:
    """
    Updates node.
    """
    ensure_admin_permissions(current_user=current_user)
    return update_node(node=node, db_session=session)

@node_route.delete("/{node_id}", response_model=dict)
def node_delete(
    node_id: int,
    current_user: LoginDep,
    session: SessionDep
):
    """
    Deletes node.
    """
    ensure_admin_permissions(current_user=current_user)
    delete_node(node_id=node_id, db_session=session)
    return {'detail': 'Node deleted'}

@node_route.post("/add_resource", response_model=NodeResponse)
def node_add_resource(
    resource_request: NodeProvidesResourceRequest,
    current_user: LoginDep,
    session: SessionDep
) -> NodeResponse:
    """
    Adds resource to node.
    """
    ensure_admin_permissions(current_user=current_user)
    return add_resource_to_node(
        request=resource_request,
        db_session=session
    )

@node_route.post("/remove_resource", response_model=NodeResponse)
def node_remove_resource(
    resource_request: NodeProvidesResourceRequest,
    current_user: LoginDep,
    session: SessionDep
) -> NodeResponse:
    """
    Removes resource from node.
    """
    ensure_admin_permissions(current_user=current_user)
    return remove_resource_from_node(
        request=resource_request,
        db_session=session
    )
