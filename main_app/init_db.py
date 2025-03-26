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
    Limit,
    NodeIsLimitedBy,
    UserHasNotification,
    GroupHasNotification,
    NotificationType,
    ResourcePanelTemplate
)
from src.app_logic.authentication import get_password_hash
import argparse
from sqlalchemy import Engine
from sqlmodel import Session
import json

def insert_default_data(engine: Engine) -> None:
    with Session(bind=engine) as session:
        everyone_group = Group(
            name="Everyone",
            users_share_statistics=True
        )
        admins = Group(
            name="Administrators",
            users_share_statistics=True,
            parent=everyone_group
        )
        users = Group(
            name="Users",
            users_share_statistics=True,
            parent=everyone_group
        )
        session.add_all([everyone_group, admins, users])
        user = User(
            name="Admin",
            surname="Admin",
            email="admin@localhost",
            username="admin",
            password=get_password_hash("admin"),
            uid=0,
            group=admins
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
            password=get_password_hash("test"),
            uid=1000
        ))
#        session.add(NodeDashboardTemplate(
#            name="Node dashboard",
#            template=json.dumps({
#                "dashboard": {
#                    "id": None,
#                    "uid": None,
#                    "title": "Node ${node_name} overview",
#                    "tags": [ "${node_name}", "${node_id}" ],
#                    "timezone": "browser",
#                    "schemaVersion": 16,
#                    "refresh": "30s"
#                },
#                "folderUid": "",
#                "message": "",
#                "overwrite": True
#            })
#        ))
        session.commit()
        session.add(Node(
            name="localhost",
            description="Test node",
            dashboard_template_id=1
        ))
        session.add(Node(
            name="192.168.122.84",
            description="Test node 2",
            dashboard_template_id=1
        ))
        session.add(Resource(
            name="CPU Cores",
            description="Test resource 1",
            notificaions=[session.get(Notification, 1)]
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
        cpu_treshold_template = open("../grafana_templates/CPU_Notificaion_template.json", "r")
        session.add(Notification(
            name="Default user CPU threshold",
            type=NotificationType.grafana_resource_exceedance_task,
            default_amount=1,
            receivers_groups=[session.get(Group, 1)],
            resource=session.get(Resource, 1),
            notification_template=cpu_treshold_template.read()
        ))
        cpu_treshold_template.close()
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
