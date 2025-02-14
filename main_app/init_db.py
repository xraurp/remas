#!/usr/bin/env python3
from src.db.connection import (
    init_db_engine,
    init_db_model,
    get_db_engine,
    drop_db_model
)
from src.db.models import (
    User,
    Group,
    Node,
    Resource,
    ResourceAlias,
    ResourceHasAlias,
    NodeProvidesResource,
    ResourceAllocation,
    Task,
    TaskTag,
    TaskHasTag,
    EventType,
    Event,
    Notification,
    EventHasNotificaton,
    Limit,
    NodeIsLimitedBy
)
import argparse
from sqlalchemy import Engine
from sqlmodel import Session

def insert_default_data(engine: Engine) -> None:
    with Session(bind=engine) as session:
        common_group = Group(
            name="Common",
            users_share_statistics=True
        )
        admins = Group(
            name="Administrators",
            users_share_statistics=True,
            parent=common_group
        )
        users = Group(
            name="Users",
            users_share_statistics=True,
            parent=common_group
        )
        session.add_all([common_group, admins, users])
        user = User(
            name="Admin",
            surname="Admin",
            email="admin@localhost",
            username="admin",
            password="admin"
        )
        session.add(user)
        session.commit()
        session.close()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--drop",
        help="Drop existing database",
        action="store_true"
    )
    parser.add_argument(
        "--init",
        help="Initialize new database",
        action="store_true"
    )
    parser.add_argument(
        "--init-data",
        help="Initialize new database with default data",
        action="store_true"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    init_db_engine()
    if args.drop:
        drop_db_model(get_db_engine())
    if args.init:
        init_db_model(get_db_engine())
    if args.init_data:
        insert_default_data(get_db_engine())

if __name__ == '__main__':
    main()
