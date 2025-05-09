from src.db.models import Limit, User, Group, Node, Resource
from sqlmodel import select, Session
from src.schemas.limit_entities import LimitRequest, LimitResponse
from fastapi import HTTPException, status
from sqlalchemy.exc import NoResultFound, IntegrityError
from src.schemas.authentication_entities import CurrentUserInfo
from src.app_logic.authentication import insufficientPermissionsException

# TODO - when adding limit, check if node is limited by diferent
#        limit in the same group / user

def get_limit_response(limit: Limit) -> LimitResponse:
    """
    Returns limit response
    """
    return LimitResponse(
        id=limit.id,
        name=limit.name,
        description=limit.description,
        amount=limit.amount,
        user_id=limit.user_id,
        group_id=limit.group_id,
        resource_id=limit.resource_id,
        node_ids=[node.id for node in limit.nodes]
    )

def get_all_limits(session: Session) -> list[LimitResponse]:
    """
    Returns all limits
    """
    limits = session.scalars(select(Limit)).all()
    results = []
    for limit in limits:
        results.append(get_limit_response(limit))
    return results

def get_limits_by_user(user_id: int, session: Session) -> list[LimitResponse]:
    """
    Returns limits by user id
    """
    limits = session.scalars(
        select(Limit).where(Limit.user_id == user_id)
    ).all()
    results = []
    for limit in limits:
        results.append(get_limit_response(limit))
    return results

def get_limits_by_group(group_id: int, session: Session) -> list[LimitResponse]:
    """
    Returns limits by group id
    """
    limits = session.scalars(
        select(Limit).where(Limit.group_id == group_id)
    ).all()
    results = []
    for limit in limits:
        results.append(get_limit_response(limit))
    return results

def get_limit(limit_id: int, session: Session) -> LimitResponse:
    """
    Returns limit by id
    """
    try:
        result = session.scalars(
            select(Limit).where(Limit.id == limit_id)
        ).one()
        return get_limit_response(result)
    except NoResultFound:
        raise HTTPException(
            status_code=404,
            detail=f"Limit with id {limit_id} not found!"
        )

def add_limit(limit: LimitRequest, session: Session) -> LimitResponse:
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
    try:
        session.add(new_limit)
        session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to create limit in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    session.refresh(new_limit)
    return get_limit_response(limit=new_limit)

def update_limit(limit: LimitRequest, session: Session) -> LimitResponse:
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
    
    if not limit.user_id and not limit.group_id:
        raise HTTPException(
            status_code=400,
            detail="Limit must have either user or group specified!"
        )
    db_limit.name = limit.name
    db_limit.description = limit.description
    db_limit.amount = limit.amount

    if limit.user_id:
        try:
            user = session.scalars(
                select(User).where(User.id == limit.user_id)
            ).one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail=f"User with id {limit.user_id} not found!"
            )
        db_limit.user = user
    else:
        db_limit.user = None
    
    if limit.group_id:
        try:
            group = session.scalars(
                select(Group).where(Group.id == limit.group_id)
            ).one()
        except NoResultFound:
            raise HTTPException(
                status_code=404,
                detail=f"Group with id {limit.group_id} not found!"
            )
        db_limit.group = group
    else:
        db_limit.group = None
    
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
    try:
        session.commit()
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Failed to update limit in database due to conflict:"
                   f"\n{e.orig.pgerror}"
        )
    session.refresh(db_limit)
    return get_limit_response(limit=db_limit)

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

def get_limit_dict(entity_limits: list[Limit]) -> dict[int, dict[int, Limit]]:
    """
    Returns most restrictive limits from the list.
    :param entity_limits (list[Limit]): list of limits for group or user
    :return (dict[int, dict[int, Limit]]): limits addressed by resource and node
    """
    limits = {}
    for limit in entity_limits:
        for node in limit.nodes:
            if limit.resource_id not in limits:
                limits[limit.resource_id] = {}
            for node in limit.nodes:
                # if there are multiple limits for the same resource and node
                # only the most restrictive limit applies
                if node.id in limits[limit.resource_id]:
                    if limits[limit.resource_id][node.id].amount < limit.amount:
                        limits[limit.resource_id][node.id] = limit
                else:
                    limits[limit.resource_id][node.id] = limit
    return limits

def merge_limit_dicts(
    parent_limits: dict[int, dict[int, Limit]],
    child_limits: dict[int, dict[int, Limit]]
) -> dict[int, dict[int, Limit]]:
    """
    Merges two limit dicts. Child limits take priority over parent.
    :param parent_limits (dict[int, dict[int, Limit]]): parent limits
    :param child_limits (dict[int, dict[int, Limit]]): child limits
    :return (dict[int, dict[int, Limit]]): merged limits
    """
    if not parent_limits:
        return child_limits
    
    for resource_id in child_limits:
        for node_id in child_limits[resource_id]:
            if resource_id not in parent_limits:
                parent_limits[resource_id] = {}
            parent_limits[resource_id][node_id] = child_limits[resource_id][node_id]
    return parent_limits

def get_all_group_limits_dict(
    group_id: int,
    session: Session
) -> dict[int, dict[int, Limit]]:
    """
    Returns all effective group limits. Effective limits are limits that are not
    overriden by another from subgroup. (Limit in child takes priority over
    parent. If there are two limits for the same resource and node in child
    the most restrictive limit applies.)
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
        parent_limits = get_all_group_limits_dict(
            group_id=group.parent_id,
            session=session
        )
    else:
        parent_limits = {}

    limits = get_limit_dict(entity_limits=group.limits)
    return merge_limit_dicts(
        parent_limits=parent_limits,
        child_limits=limits
    )

def get_all_user_limits_dict(
    user_id: int,
    session: Session
) -> dict[int, dict[int, Limit]]:
    """
    Returns all effective user limits. Effective limits are limits that are not
    overriden by another from group. (Limit in user takes priority over
    group. If there are two limits for the same resource and node in user
    the most restrictive limit applies.)
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
    
    group_limits = get_all_group_limits_dict(
        group_id=user.group_id,
        session=session
    )

    limits = get_limit_dict(entity_limits=user.limits)
    return merge_limit_dicts(
        parent_limits=group_limits,
        child_limits=limits
    )

def get_all_group_limits_list(
    group_id: int,
    current_user: CurrentUserInfo,
    session: Session
) -> list[LimitResponse]:
    """
    Returns all group limits
    :param group_id (int): group id
    :param current_user (CurrentUserInfo): current user
    :param session (Session): database session
    :return (list[LimitResponse]): group limits
    """
    if not current_user.is_admin:
        user = session.get(User, current_user.user_id)
        if not user.group_id == group_id:
            raise insufficientPermissionsException
    
    limits = get_all_group_limits_dict(
        group_id=group_id,
        session=session
    )

    limit_list = []
    for resource_id, nodes in limits.items():
        for node_id, limit in nodes.items():
            lim_response = get_limit_response(limit=limit)
            if lim_response not in limit_list:
                limit_list.append(lim_response)
    return limit_list

def get_all_user_limits_list(
    user_id: int,
    current_user: CurrentUserInfo,
    session: Session
) -> list[LimitResponse]:
    """
    Returns all user limits
    :param user_id (int): user id
    :param current_user (CurrentUserInfo): current user
    :param session (Session): database session
    :return (list[LimitResponse]): user limits
    """
    if not current_user.is_admin and not current_user.user_id == user_id:
        raise insufficientPermissionsException

    limits = get_all_user_limits_dict(
        user_id=user_id,
        session=session
    )

    limit_list = []
    for resource_id, nodes in limits.items():
        for node_id, limit in nodes.items():
            lim_response = get_limit_response(limit=limit)
            if lim_response not in limit_list:
                limit_list.append(lim_response)
    return limit_list
