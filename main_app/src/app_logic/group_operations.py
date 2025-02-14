from src.db.models import Group, User
from sqlmodel import select, Session

# TODO - query notifications when receiving group

def create_group(
    group: Group,
    db_session: Session
) -> Group:
    """
    Creates new group.
    """
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group

def get_group(group_id: int, db_session: Session) -> Group:
    """
    Returns group by id.
    """
    return db_session.get(Group, group_id)

def get_all_groups(db_session: Session) -> list[Group]:
    """
    Returns all groups.
    """
    return db_session.scalars(select(Group)).all()

def update_group(group: Group, db_session: Session) -> Group:
    """
    Updates group.
    """
    db_group = db_session.get(Group, group.id)
    if not db_group:
        raise ValueError(f"Group with id {group.id} not found!")
    db_group.name = group.name
    db_group.description = group.description
    db_group.users_share_statistics = group.users_share_statistics
    db_session.commit()
    db_session.refresh(db_group)
    return db_group

def delete_group(group_id: int, db_session: Session) -> None:
    """
    Deletes group.
    """
    if group_id <= 3:
        raise ValueError("Cannot delete default groups!")
    db_group = db_session.get(Group, group_id)
    if not db_group:
        raise ValueError(f"Group with id {group_id} not found!")
    gid = 3  # User group
    if db_group.parent_id:
        gid = db_group.parent_id
    for user in db_group.members:
        user.group_id = gid
    db_session.commit()
    db_session.delete(db_group)
    db_session.commit()

def add_users_to_group(
    group_id: int,
    user_ids: list[int],
    db_session: Session
) -> Group:
    """
    Adds users to group.
    """
    group = db_session.get(Group, group_id)
    if not group:
        raise ValueError(f"Group with id {group_id} not found!")
    for user_id in user_ids:
        user = db_session.get(User, user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found!")
        group.members.append(user)
    db_session.commit()
    db_session.refresh(group)
    return group

def change_group_parent(
    group_id: int,
    parent_id: int,
    db_session: Session
) -> Group:
    """
    Changes group parent.
    """
    group = db_session.get(Group, group_id)
    parent = db_session.get(Group, parent_id)
    if not group:
        raise ValueError(f"Group with id {group_id} not found!")
    if not parent:
        raise ValueError(f"Group with id {parent_id} not found!")
    group.parent_id = parent_id
    db_session.commit()
    db_session.refresh(group)
    return group
