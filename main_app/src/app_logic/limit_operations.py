from src.db.models import Limit, User, Group, Node, Resource
from sqlmodel import select, Session
from src.schemas.limit_entities import LimitRequest, LimitResponse
from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

def get_limits_by_user(user_id: int, session: Session) -> list[Limit]:
    """
    Returns limits by user id
    """
    return session.scalars(select(Limit).where(Limit.user_id == user_id)).all()

def get_limits_by_group(group_id: int, session: Session) -> list[Limit]:
    """
    Returns limits by group id
    """
    return session.scalars(
        select(Limit).where(Limit.group_id == group_id)
    ).all()

def get_limit(limit_id: int, session: Session) -> Limit:
    """
    Returns limit by id
    """
    return session.scalars(select(Limit).where(Limit.id == limit_id)).one()

def add_limit(limit: LimitRequest, session: Session) -> Limit:
    """
    Adds limit
    """
    if limit.user_id and limit.group_id:
        raise HTTPException(
            status_code=400,
            detail="Limit can't have both user_id and group_id "
                   "specified at the same time!"
        )
    if not limit.user_id and not limit.group_id:
        raise HTTPException(
            status_code=400,
            detail="Limit must have either user_id or group_id specified!"
        )
    user = session.scalars(select(User).where(User.id == limit.user_id)).first()
    group = session.scalars(
        select(Group).where(Group.id == limit.group_id)
    ).first()
    if limit.user_id and not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {limit.user_id} not found!"
        )
    if limit.group_id and not group:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {limit.group_id} not found!"
        )
    
    try:
        resource = session.scalars(
            select(Resource).where(Resource.id == limit.resource_id)
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {limit.resource_id} not found!"
        )
    
    nodes = session.scalars(
        select(Node).where(Node.id.in_(limit.node_ids))
    ).all()

    new_limit = Limit(
        name=limit.name,
        description=limit.description,
        amount=limit.amount,
        user=user,
        group=group,
        resource=resource,
        nodes=nodes
    )
    session.add(new_limit)
    session.commit()
    session.refresh(new_limit)
    return new_limit

def update_limit(limit: LimitRequest, session: Session) -> Limit:
    """
    Updates limit
    """
    try:
        db_limit = session.scalars(
            select(Limit).where(Limit.id == limit.id)
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Limit with id {limit.id} not found!"
        )
    db_limit.name = limit.name
    db_limit.description = limit.description
    db_limit.amount = limit.amount
    try:
        resource = session.scalars(
            select(Resource).where(Resource.id == limit.resource_id)
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Resource with id {limit.resource_id} not found!"
        )
    nodes = session.scalars(
        select(Node).where(Node.id.in_(limit.node_ids))
    ).all()
    db_limit.nodes = nodes
    db_limit.resource = resource
    session.commit()
    session.refresh(db_limit)
    return db_limit

def remove_limit(limit_id: int, session: Session) -> None:
    """
    Removes limit
    """
    try:
        limit = session.scalars(
            select(Limit).where(Limit.id == limit_id)
        ).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Limit with id {limit_id} not found!"
        )
    session.delete(limit)
    session.commit()

def get_all_group_limits(
    group_id: int,
    session: Session
) -> dict[int, dict[int, Limit]]:
    """
    Returns all group limits
    :param group_id (int): group id
    :param session (Session): database session
    :return (dict[int, dict[int, Limit]]): group limits by resource
    """
    try:
        group = session.scalars(select(Group).where(Group.id == group_id)).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Group with id {group_id} not found!"
        )

    if group.parent_id:
        limits = get_all_group_limits(
            group_id=group.parent_id,
            session=session
        )
    else:
        limits = {}

    for limit in group.limits:
        for node in limit.nodes:
            if limit.resource_id not in limits:
                limits[limit.resource_id] = {}
            for node in limit.nodes:
                limits[limit.resource_id][node.id] = limit

    return limits


def get_all_user_limits(
    user_id: int,
    session: Session
) -> dict[int, dict[int, Limit]]:
    """
    Returns all user limits
    :param user_id (int): user id
    :param session (Session): database session
    :return (dict[int, dict[int, Limit]]): user limits by resource
    """
    try:
        user = session.scalars(select(User).where(User.id == user_id)).one()
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found!"
        )
    
    limits = get_all_group_limits(
        group_id=user.group_id,
        session=session
    )

    for limit in user.limits:
        for node in limit.nodes:
            if limit.resource_id not in limits:
                limits[limit.resource_id] = {}
            for node in limit.nodes:
                limits[limit.resource_id][node.id] = limit

    return limits
