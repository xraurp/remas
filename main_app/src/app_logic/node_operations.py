from src.db.models import Node, NodeProvidesResource, Resource
from sqlmodel import select, Session
from src.schemas.node_entities import (
    NodeProvidesResourceRequest,
    NodeResponse,
    NodeResourceResponse
)

# TODO - query resources when receiving node

def generate_node_response(node: Node) -> NodeResponse:
    """
    Generates node response
    :param node: Node database enetity
    :return: NodeResponse including resources provided by node and their amount
    """
    node_response = NodeResponse(
        id=node.id,
        name=node.name,
        description=node.description
    )
    for resource in node.resources:
        node_response.resources.append(NodeResourceResponse(
            id=resource.resource_id,
            name=resource.resource.name,
            description=resource.resource.description,
            amount=resource.amount
        ))
    return node_response

def create_node(
    node: Node,
    db_session: Session
) -> NodeResponse:
    """
    Creates new node
    """
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return generate_node_response(node=node)

def delete_node(node_id: int, db_session: Session) -> None:
    """
    Deletes node
    """
    node = db_session.get(Node, node_id)
    if not node:
        raise ValueError(f"Node with id {node_id} not found!")
    db_session.delete(node)
    db_session.commit()

def get_node(node_id: int, db_session: Session) -> NodeResponse:
    """
    Returns node by id
    """
    result = db_session.scalars(select(Node).where(Node.id == node_id)).one()
    return generate_node_response(node=result)


def get_all_nodes(db_session: Session) -> list[NodeResponse]:
    """
    Returns all nodes
    """
    result = db_session.scalars(select(Node)).all()
    return [generate_node_response(node=node) for node in result]

def update_node(node: Node, db_session: Session) -> NodeResponse:
    """
    Updates node
    """
    db_node = db_session.get(Node, node.id)
    if not db_node:
        raise ValueError(f"Node with id {node.id} not found!")
    db_node.name = node.name
    db_node.description = node.description
    db_session.commit()
    db_session.refresh(db_node)
    return generate_node_response(node=db_node)

def add_resource_to_node(
    request: NodeProvidesResourceRequest,
    db_session: Session
) -> NodeResponse:
    """
    Adds resource to node
    """
    node = db_session.get(Node, request.node_id)
    if not node:
        raise ValueError(f"Node with id {request.node_id} not found!")
    resource = db_session.get(Resource, request.resource_id)
    if not resource:
        raise ValueError(f"Resource with id {request.resource_id} not found!")
    node.resources.append(NodeProvidesResource(
        node_id=request.node_id,
        resource_id=request.resource_id,
        amount=request.amount
    ))
    db_session.commit()
    db_session.refresh(node)
    return generate_node_response(node=node)

def remove_resource_from_node(
    request: NodeProvidesResourceRequest,
    db_session: Session
) -> NodeResponse:
    """
    Removes resource from node
    """
    node = db_session.get(Node, request.node_id)
    if not node:
        raise ValueError(f"Node with id {request.node_id} not found!")
    resource = db_session.get(Resource, request.resource_id)
    if not resource:
        raise ValueError(f"Resource with id {request.resource_id} not found!")
    node.resources.remove(NodeProvidesResource(
        node_id=request.node_id,
        resource_id=request.resource_id,
        amount=request.amount
    ))
    db_session.commit()
    db_session.refresh(node)
    return generate_node_response(node=node)
