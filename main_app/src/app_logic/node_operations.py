from src.db.models import Node, Resource, NodeProvidesResource
from sqlmodel import select, Session

# TODO - query resources when receiving node

def create_node(
    node: Node,
    db_session: Session
) -> Node:
    """
    Creates new node
    """
    db_session.add(node)
    db_session.commit()
    db_session.refresh(node)
    return node

def delete_node(node_id: int, db_session: Session) -> None:
    """
    Deletes node
    """
    node = db_session.get(Node, node_id)
    if not node:
        raise ValueError(f"Node with id {node_id} not found!")
    db_session.delete(node)
    db_session.commit()


def get_node(node_id: int, db_session: Session) -> Node:
    """
    Returns node by id
    """
    return db_session.get(Node, node_id)


def get_all_nodes(db_session: Session) -> list[Node]:
    """
    Returns all nodes
    """
    return db_session.scalars(select(Node)).all()

def update_node(node: Node, db_session: Session) -> Node:
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
    return db_node

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

def add_resource_to_node(
    resource_id: int,
    node_id: int,
    amount: int,
    db_session: Session
) -> NodeProvidesResource:
    """
    Adds resource to node
    """
    node = db_session.get(Node, node_id)
    if not node:
        raise ValueError(f"Node with id {node_id} not found!")
    resource = db_session.get(Resource, resource_id)
    if not resource:
        raise ValueError(f"Resource with id {resource_id} not found!")
    node.resources.append(NodeProvidesResource(
        node_id=node_id,
        resource_id=resource_id,
        amount=amount
    ))
    db_session.commit()
    db_session.refresh(node)
    return node
