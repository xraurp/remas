from src.db.models  import Resource
from sqlmodel import select, Session

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
