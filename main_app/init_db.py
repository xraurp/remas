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
    TaskStatus,
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

def insert_test_data(engine: Engine) -> None:
    with Session(bind=engine) as session:
        session.add(User(
            name="Test",
            surname="Test",
            email="test@localhost",
            username="test",
            password="test"
        ))
        session.add(Node(
            name="TestNode",
            description="Test node"
        ))
        session.add(Node(
            name="TestNode2",
            description="Test node 2"
        ))
        session.add(Resource(
            name="TestResource1",
            description="Test resource 1"
        ))
        session.add(Resource(
            name="TestResource2",
            description="Test resource 2"
        ))
        session.add(Resource(
            name="TestResource3",
            description="Test resource 3"
        ))
        session.add(NodeProvidesResource(
            node_id=1,
            resource_id=1,
            amount=1
        ))
        session.add(NodeProvidesResource(
            node_id=1,
            resource_id=2,
            amount=4
        ))
        session.add(NodeProvidesResource(
            node_id=2,
            resource_id=1,
            amount=2
        ))
        session.add(NodeProvidesResource(
            node_id=2,
            resource_id=2,
            amount=2
        ))
        session.add(ResourceAlias(
            name="TestAlias1",
            description="Test alias 1"
        ))
        session.add(ResourceAlias(
            name="TestAlias2",
            description="Test alias 2"
        ))
        session.commit()
        session.add(ResourceHasAlias(
            resource_id=1,
            alias_id=1
        ))
        session.add(ResourceHasAlias(
            resource_id=1,
            alias_id=2
        ))
        session.add(ResourceHasAlias(
            resource_id=2,
            alias_id=1
        ))
        session.add(ResourceHasAlias(
            resource_id=2,
            alias_id=2
        ))
        session.add(ResourceHasAlias(
            resource_id=3,
            alias_id=1
        ))
        session.add(ResourceHasAlias(
            resource_id=3,
            alias_id=2
        ))
        session.commit()
        session.add(Task(
            name="TestTask1",
            description="Test task 1",
            start_time="2025-02-16 10:00:00",
            end_time="2025-02-16 14:00:00",
            status=TaskStatus.scheduled,
            owner_id=1,
            resource_allocations=[
                ResourceAllocation(
                    node_id=2,
                    resource_id=1,
                    amount=1
                ),
                ResourceAllocation(
                    node_id=2,
                    resource_id=2,
                    amount=1
                ),
                ResourceAllocation(
                    node_id=1,
                    resource_id=2,
                    amount=1
                )
            ],
            events=[
                Event(
                    name=f"TestTask1 start",
                    description="Start test task 1",
                    time="2025-02-16 10:00:00",
                    type=EventType.task_start
                ),
                Event(
                    name=f"TestTask1 end",
                    description="End test task 1",
                    time="2025-02-16 14:00:00",
                    type=EventType.task_end
                )
            ]
        ))
        session.add(Task(
            name="TestTask2",
            description="Test task 2",
            start_time="2025-02-16 11:00:00",
            end_time="2025-02-16 15:00:00",
            status=TaskStatus.scheduled,
            owner_id=1,
            resource_allocations=[
                ResourceAllocation(
                    node_id=2,
                    resource_id=1,
                    amount=1
                ),
                ResourceAllocation(
                    node_id=2,
                    resource_id=2,
                    amount=1
                )
            ],
            events=[
                Event(
                    name=f"TestTask2 start",
                    description="Start test task 2",
                    time="2025-02-16 11:00:00",
                    type=EventType.task_start
                ),
                Event(
                    name=f"TestTask2 end",
                    description="End test task 2",
                    time="2025-02-16 15:00:00",
                    type=EventType.task_end
                )
            ]
        ))
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
    parser.add_argument(
        "--init-test",
        help="Initialize new database with test data",
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
    if args.init_test:
        insert_test_data(get_db_engine())

if __name__ == '__main__':
    main()
