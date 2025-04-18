from src.db.models import Node, NodeProvidesResource, Resource
from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError
from src.schemas.node_entities import (
    NodeProvidesResourceRequest,
    NodeResponse,
    NodeResourceResponse
)
from src.app_logic.grafana_alert_operations import (
    update_grafana_alert_for_all_users_and_groups,
    grafana_remove_alert_for_node
)
from fastapi import HTTPException, status

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
            amount=resource.amount,
            unit=resource.resource.unit
        ))
    return node_response

def create_node(
    node: Node,
    db_session: Session
) -> NodeResponse:
    """
    Creates new node
    """
    node.id = None
    node.resources = []

    try:
        db_session.add(node)
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create node in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    db_session.refresh(node)
    # TODO - add node dashboard to Grafana
    return generate_node_response(node=node)

def delete_node(node_id: int, db_session: Session) -> None:
    """
    Deletes node
    """
    node = db_session.get(Node, node_id)
    if not node:
        raise HTTPException(
            status_code=404,
            detail=f"Node with id {node_id} not found!"
        )
    # remove all Grafana alerts for node
    for npr in node.resources:
        resource = npr.resource
        for notification in resource.notifications:
            grafana_remove_alert_for_node(
                node=node,
                notification=notification
            )
    # TODO - remove node dashboard from Grafana
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
        raise HTTPException(
            status_code=404,
            detail=f"Node with id {node.id} not found!"
        )
    db_node.name = node.name
    db_node.description = node.description
    # TODO - update alerts in Grafana
    # TODO - update node dashboard in Grafana
    try:
        db_session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to update node in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
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
        raise HTTPException(
            status_code=404,
            detail=f"Node with id {request.node_id} not found!"
        )
    resource = db_session.get(Resource, request.resource_id)
    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {request.resource_id} not found!"
        )
    npr = db_session.get(
        NodeProvidesResource,
        (request.node_id, request.resource_id)
    )
    if npr:
        # update existing node resource
        npr.amount = request.amount
    else:
        # add new node resource
        node.resources.append(NodeProvidesResource(
            node_id=request.node_id,
            resource_id=request.resource_id,
            amount=request.amount
        ))
    db_session.commit()
    db_session.refresh(node)
    # add Grafana alerts for node
    for notification in resource.notifications:
        update_grafana_alert_for_all_users_and_groups(
            notification=notification,
            db_session=db_session
        )
    # TODO - add resource panels to node dashboard
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
        raise HTTPException(
            status_code=404,
            detail=f"Node with id {request.node_id} not found!"
        )
    resource = db_session.get(Resource, request.resource_id)
    if not resource:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {request.resource_id} not found!"
        )
    npr = db_session.get(
        NodeProvidesResource,
        (request.node_id, request.resource_id)
    )
    if not npr:
        raise HTTPException(
            status_code=404,
            detail=f"Node with id {request.node_id} doesn't have "
                   f"resource with id {request.resource_id}!"
        )
    db_session.delete(npr)
    db_session.commit()
    db_session.refresh(node)
    # remove Grafana alerts for node
    for notification in resource.notifications:
        grafana_remove_alert_for_node(
            node=node,
            notification=notification
        )
    # TODO - remove resource panels to node dashboard
    return generate_node_response(node=node)
