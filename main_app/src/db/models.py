from typing import Optional
from sqlmodel import (
    Field,
    SQLModel,
    Relationship
)
import enum
from datetime import datetime


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str | None = None
    surname: str | None = None
    username: str = Field(unique=True, index=True)
    password: str
    email: str = Field(index=True)

    # User is by default member of group 2 ("users")
    group_id: int = Field(default=2, foreign_key="group.id")
    group: "Group" = Relationship(back_populates="members")

    limits: list["Limit"] = Relationship(back_populates="user")
    tasks: list["Task"] = Relationship(back_populates="owner")
    tags: list["TaskTag"] = Relationship(back_populates="user")
    # Notifications created by this user
    created_notifications: list["Notification"] = Relationship(
        back_populates="owner"
    )

    # Received notifications
    notifications: list["UserHasNotification"] = Relationship(
        back_populates="user"
    )

class Group(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    users_share_statistics: bool = True

    # Self reference - parent / child relationship
    parent_id: int | None = Field(default=None, foreign_key='group.id')
    parent: Optional["Group"] = Relationship(
        back_populates='children',
        sa_relationship_kwargs={'remote_side': 'Group.id'}
    )
    children: list["Group"] = Relationship(back_populates='parent')

    members: list[User] = Relationship(back_populates="group")
    limits: list["Limit"] = Relationship(back_populates="group")

    notifications: list["GroupHasNotification"] = Relationship(
        back_populates="group"
    )

class Node(SQLModel, table=True):
    """
    Node is a computer in the cluster.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list["NodeProvidesResource"] = Relationship(back_populates="node")
    resource_allocations: list["ResourceAllocation"] = Relationship(
        back_populates="node"
    )
    limits: list["NodeIsLimitedBy"] = Relationship(back_populates="node")

class Resource(SQLModel, table=True):
    """
    Resource is provided by a node, like CPU, RAM, GPU, etc.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    nodes: list["NodeProvidesResource"] = Relationship(back_populates="resource")
    resource_allocations: list["ResourceAllocation"] = Relationship(
        back_populates="resource"
    )
    limits: list["Limit"] = Relationship(back_populates="resource")
    aliases: list["ResourceHasAlias"] = Relationship(back_populates="resource")

class ResourceAlias(SQLModel, table=True):
    """
    Alias is an additional name for a resource, like "cpu" or "gpu".
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list["ResourceHasAlias"] = Relationship(back_populates="alias")

class ResourceHasAlias(SQLModel, table=True):
    """
    Connection table between resource and alias.
    """
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True
    )
    alias_id: int = Field(
        default=None,
        foreign_key="resourcealias.id",
        primary_key=True
    )

    resource: Resource = Relationship(back_populates="aliases")
    alias: ResourceAlias = Relationship(back_populates="resources")

class NodeProvidesResource(SQLModel, table=True):
    """
    Connection table for node and resource. Defines how much of a resource
    is provided by a node (for example 2 GPUs).
    """
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True
    )
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True
    )
    amount: int

    node: Node = Relationship(back_populates="resources")
    resource: Resource = Relationship(back_populates="nodes")

class ResourceAllocation(SQLModel, table=True):
    """
    ResourceAllocation is a connection table between node, resource and task.
    Tells how much of a resource is used by a task on a node.
    """
    task_id: int = Field(
        default=None,
        foreign_key="task.id",
        primary_key=True
    )
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True
    )
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True
    )
    amount: int

    task: "Task" = Relationship(back_populates="resource_allocations")
    node: Node = Relationship(back_populates="resource_allocations")
    resource: Resource = Relationship(back_populates="resource_allocations")

class Task(SQLModel, table=True):
    """
    Task is a job that user executes on a node.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: User = Relationship(back_populates="tasks")

    resource_allocations: list[ResourceAllocation] = Relationship(
        back_populates="task"
    )
    tags: list["TaskHasTag"] = Relationship(back_populates="task")
    events: list["Event"] = Relationship(back_populates="task")

class TaskTag(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    user_id: int = Field(default=None, foreign_key="user.id")
    user: User = Relationship(back_populates="tags")
    tasks: list["TaskHasTag"] = Relationship(back_populates="tag")

class TaskHasTag(SQLModel, table=True):
    task_id: int = Field(
        default=None,
        foreign_key="task.id",
        primary_key=True
    )
    tag_id: int = Field(
        default=None,
        foreign_key="tasktag.id",
        primary_key=True
    )

    task: Task = Relationship(back_populates="tags")
    tag: TaskTag = Relationship(back_populates="tasks")

class EventType(enum.Enum):
    task_start = "task_start"
    task_end = "task_end"
    other = "other"

class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    time: datetime = Field(index=True)
    type: EventType = Field(default=EventType.other)

    task_id: int = Field(default=None, foreign_key="task.id")
    task: Task = Relationship(back_populates="events")
    notifications: list["EventHasNotificaton"] = Relationship(
        back_populates="event"
    )

class Notification(SQLModel, table=True):
    """
    Notification for time based events like task start/end.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    # Time offset in seconds
    time_offset: int | None = Field(default=None)
    notification_content: str | None = None

    # User that created the notification
    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: User = Relationship(back_populates="created_notifications")
    events: list["EventHasNotificaton"] = Relationship(
        back_populates="notification"
    )

    receivers_users: list["UserHasNotification"] = Relationship(
        back_populates="notification"
    )
    receivers_groups: list["GroupHasNotification"] = Relationship(
        back_populates="notification"
    )

class UserHasNotification(SQLModel, table=True):
    user_id: int = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True
    )

    user: User = Relationship(back_populates="notifications")
    notification: Notification = Relationship(back_populates="receivers_users")

class GroupHasNotification(SQLModel, table=True):
    group_id: int = Field(
        default=None,
        foreign_key="group.id",
        primary_key=True
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True
    )

    group: Group = Relationship(back_populates="notifications")
    notification: Notification = Relationship(back_populates="receivers_groups")

class EventHasNotificaton(SQLModel, table=True):
    """
    Connection table between event and notification.
    """
    event_id: int = Field(
        default=None,
        foreign_key="event.id",
        primary_key=True
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True
    )

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
    nodes: list["NodeIsLimitedBy"] = Relationship(back_populates="limit")

class NodeIsLimitedBy(SQLModel, table=True):
    """
    Connection table for limit and node.
    """
    limit_id: int = Field(
        default=None,
        foreign_key="limit.id",
        primary_key=True
    )
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True
    )

    limit: Limit = Relationship(back_populates="nodes")
    node: Node = Relationship(back_populates="limits")
