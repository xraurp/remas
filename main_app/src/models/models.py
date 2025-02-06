from typing import Literal
from sqlmodel import (
    Field,
    SQLModel,
    Relationship,
    create_engine
)
from datetime import (
    datetime,
    timedelta
)


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str | None = None
    surname: str | None = None
    username: str = Field(unique=True, index=True)
    password: str
    email: str = Field(index=True)

    # User is by default member of group 2 ("users")
    group_id: int = Field(default=2, foreign_key="group.id")
    group: Group = Relationship(back_populates="users")

    limits: list[Limit] = Relationship(back_populates="user")
    tasks: list[Task] = Relationship(back_populates="user")
    tags: list[TaskTag] = Relationship(back_populates="user")

class Group(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    users_share_statistics: bool = True

    parent_id: int | None = Field(default=None, foreign_key='group.id')
    parent: Group | None = Relationship(back_populates='children')
    children: list[Group] = Relationship(back_populates='parent')

    users: list[User] = Relationship(back_populates="group")
    limits: list[Limit] = Relationship(back_populates="group")

class Node(SQLModel, table=True):
    """
    Node is a computer in the cluster.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list[NodeProvidesResource] = Relationship(back_populates="node")
    resource_allocations: list[ResourceAllocation] = Relationship(
        back_populates="node"
    )
    limits: list[NodeIsLimitedBy] = Relationship(back_populates="node")

class Resource(SQLModel, table=True):
    """
    Resource is provided by a node, like CPU, RAM, GPU, etc.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    nodes: list[NodeProvidesResource] = Relationship(back_populates="resource")
    resource_allocations: list[ResourceAllocation] = Relationship(
        back_populates="resource"
    )
    limits: list[Limit] = Relationship(back_populates="resource")
    aliases: list[ResourceHasAlias] = Relationship(back_populates="resource")

class ResourceAlias(SQLModel, table=True):
    """
    Alias is an additional name for a resource, like "cpu" or "gpu".
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list[ResourceHasAlias] = Relationship(back_populates="alias")

class ResourceHasAlias(SQLModel, table=True):
    """
    Connection table between resource and alias.
    """
    resource_id: int = Field(default=None, foreign_key="resource.id")
    alias_id: int = Field(default=None, foreign_key="resource_alias.id")

    resource: Resource = Relationship(back_populates="aliases")
    alias: ResourceAlias = Relationship(back_populates="resources")

class NodeProvidesResource(SQLModel, table=True):
    """
    Connection table for node and resource. Defines how much of a resource
    is provided by a node (for example 2 GPUs).
    """
    node_id: int = Field(default=None, foreign_key="node.id")
    resource_id: int = Field(default=None, foreign_key="resource.id")
    amount: int

    node: Node = Relationship(back_populates="resources")
    resource: Resource = Relationship(back_populates="nodes")

class ResourceAllocation(SQLModel, table=True):
    """
    ResourceAllocation is a connection table between node, resource and task.
    Tells how much of a resource is used by a task on a node.
    """
    node_id: int = Field(default=None, foreign_key="node.id")
    resource_id: int = Field(default=None, foreign_key="resource.id")
    task_id: int = Field(default=None, foreign_key="task.id")
    amount: int

    node: Node = Relationship(back_populates="resource_allocations")
    resource: Resource = Relationship(back_populates="resource_allocations")
    task: Task = Relationship(back_populates="resource_allocations")

class Task(SQLModel, table=True):
    """
    Task is a job that user executes on a node.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    user_id: int = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="tasks", description="Task owner")

    resource_allocations: list[ResourceAllocation] = Relationship(
        back_populates="task"
    )
    tags: list[TaskTag] = Relationship(back_populates="tasks")
    events: list[Event] = Relationship(back_populates="task")

class TaskTag(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    user_id: int = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="tags")
    tasks: list[TaskHasTag] = Relationship(back_populates="tag")

class TaskHasTag(SQLModel, table=True):
    task_id: int = Field(default=None, foreign_key="task.id")
    tag_id: int = Field(default=None, foreign_key="task_tag.id")

    task: Task = Relationship(back_populates="tags")
    tag: TaskTag = Relationship(back_populates="tasks")

class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    time: datetime = Field(index=True)
    type: Literal["task_start", "task_end", "other"] = "other"

    task_id: int = Field(default=None, foreign_key="task.id")
    task: Task = Relationship(back_populates="events")
    notifications: list[EventHasNotificaton] = Relationship(back_populates="event")

class Notification(SQLModel, table=True):
    """
    Notification for time based events like task start/end.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    time_offset: int | None = Field(
        default=None,
        description="Time offset in seconds"
    )
    notification_content: str | None = None

    events: list[EventHasNotificaton] = Relationship(back_populates="notification")

class EventHasNotificaton(SQLModel, table=True):
    """
    Connection table between event and notification.
    """
    event_id: int = Field(default=None, foreign_key="event.id")
    notification_id: int = Field(default=None, foreign_key="notification.id")

    event: Event = Relationship(back_populates="notifications")
    notification: Notification = Relationship(back_populates="events")

# TODO - add automatic reaction to events?

class Limit(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    amount: int

    # Either user or group must be set
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="limits")
    group_id: int | None = Field(default=None, foreign_key="group.id")
    group: Group | None = Relationship(back_populates="limits")

    resource_id: int = Field(default=None, foreign_key="resource.id")
    resource: Resource = Relationship(back_populates="limits")
    nodes: list[NodeIsLimitedBy] = Relationship(back_populates="limit")

class NodeIsLimitedBy(SQLModel, table=True):
    """
    Connection table for limit and node.
    """
    limit_id: int = Field(default=None, foreign_key="limit.id")
    node_id: int = Field(default=None, foreign_key="node.id")

    limit: Limit = Relationship(back_populates="nodes")
    node: Node = Relationship(back_populates="limits")


def init_db() -> None:
    from ..config import Settings

    engine = create_engine(Settings.database_url, echo=True)
    SQLModel.metadata.create_all(engine)

if __name__ == '__main__':
    init_db()
