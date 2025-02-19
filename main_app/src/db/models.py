from typing import Optional
from sqlmodel import (
    Field,
    SQLModel,
    Relationship
)
import enum
from datetime import datetime


class UserHasNotification(SQLModel, table=True):
    user_id: int = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True,
        ondelete="CASCADE"
    )

class GroupHasNotification(SQLModel, table=True):
    group_id: int = Field(
        default=None,
        foreign_key="group.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True,
        ondelete="CASCADE"
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
    group: "Group" = Relationship(back_populates="members")

    limits: list["Limit"] = Relationship(
        back_populates="user",
        cascade_delete=True
    )
    tasks: list["Task"] = Relationship(
        back_populates="owner",
        cascade_delete=True
    )
    tags: list["TaskTag"] = Relationship(
        back_populates="user",
        cascade_delete=True
    )
    # Notifications created by this user
    created_notifications: list["Notification"] = Relationship(
        back_populates="owner",
        cascade_delete=True
    )

    # Received notifications
    notifications: list["Notification"] = Relationship(
        back_populates="receivers_users",
        link_model=UserHasNotification
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

    notifications: list["Notification"] = Relationship(
        back_populates="receivers_groups",
        link_model=GroupHasNotification
    )

class NodeIsLimitedBy(SQLModel, table=True):
    """
    Connection table for limit and node.
    """
    limit_id: int = Field(
        default=None,
        foreign_key="limit.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True,
        ondelete="CASCADE"
    )

class Node(SQLModel, table=True):
    """
    Node is a computer in the cluster.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list["NodeProvidesResource"] = Relationship(
        back_populates="node",
        cascade_delete=True
    )
    resource_allocations: list["ResourceAllocation"] = Relationship(
        back_populates="node"
    )
    limits: list["Limit"] = Relationship(
        back_populates="nodes",
        link_model=NodeIsLimitedBy
    )

class ResourceHasAlias(SQLModel, table=True):
    """
    Connection table between resource and alias.
    """
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    alias_id: int = Field(
        default=None,
        foreign_key="resourcealias.id",
        primary_key=True,
        ondelete="CASCADE"
    )

class Resource(SQLModel, table=True):
    """
    Resource is provided by a node, like CPU, RAM, GPU, etc.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    nodes: list["NodeProvidesResource"] = Relationship(
        back_populates="resource",
        cascade_delete=True
    )
    resource_allocations: list["ResourceAllocation"] = Relationship(
        back_populates="resource"
    )
    limits: list["Limit"] = Relationship(back_populates="resource")
    aliases: list["ResourceAlias"] = Relationship(
        back_populates="resources",
        link_model=ResourceHasAlias
    )

class ResourceAlias(SQLModel, table=True):
    """
    Alias is an additional name for a resource, like "cpu" or "gpu".
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    resources: list["Resource"] = Relationship(
        back_populates="aliases",
        link_model=ResourceHasAlias
    )

class NodeProvidesResource(SQLModel, table=True):
    """
    Connection table for node and resource. Defines how much of a resource
    is provided by a node (for example 2 GPUs).
    """
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True,
        ondelete="CASCADE"
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
        primary_key=True,
        ondelete="CASCADE"
    )
    node_id: int = Field(
        default=None,
        foreign_key="node.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    amount: int

    task: "Task" = Relationship(back_populates="resource_allocations")
    node: Node = Relationship(back_populates="resource_allocations")
    resource: Resource = Relationship(back_populates="resource_allocations")

class TaskHasTag(SQLModel, table=True):
    task_id: int = Field(
        default=None,
        foreign_key="task.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    tag_id: int = Field(
        default=None,
        foreign_key="tasktag.id",
        primary_key=True,
        ondelete="CASCADE"
    )

class TaskStatus(enum.Enum):
    scheduled = "scheduled"
    running = "running"
    finished = "finished"

class Task(SQLModel, table=True):
    """
    Task is a job that user executes on a node.
    """
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    start_time: datetime = Field(index=True)
    end_time: datetime = Field(index=True)

    status: TaskStatus = Field(default=TaskStatus.scheduled, index=True)

    owner_id: int = Field(
        default=None,
        foreign_key="user.id",
        ondelete="CASCADE"
    )
    owner: User = Relationship(back_populates="tasks")

    resource_allocations: list[ResourceAllocation] = Relationship(
        back_populates="task",
        cascade_delete=True
    )
    tags: list["TaskTag"] = Relationship(
        back_populates="tasks",
        link_model=TaskHasTag
    )
    events: list["Event"] = Relationship(
        back_populates="task",
        cascade_delete=True
    )

class TaskTag(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None

    user_id: int = Field(
        default=None,
        foreign_key="user.id",
        ondelete="CASCADE"
    )
    user: User = Relationship(back_populates="tags")
    tasks: list[Task] = Relationship(
        back_populates="tags",
        link_model=TaskHasTag
    )

class EventType(enum.Enum):
    task_start = "task_start"
    task_end = "task_end"
    other = "other"

'''
class EventHasNotificaton(SQLModel, table=True):
    """
    Connection table between event and notification.
    """
    event_id: int = Field(
        default=None,
        foreign_key="event.id",
        primary_key=True,
        ondelete="CASCADE"
    )
    notification_id: int = Field(
        default=None,
        foreign_key="notification.id",
        primary_key=True,
        ondelete="CASCADE"
    )
'''

class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str | None = None
    time: datetime = Field(index=True)
    type: EventType = Field(default=EventType.other)

    task_id: int = Field(
        default=None,
        foreign_key="task.id",
        ondelete="CASCADE"
    )
    task: Task = Relationship(back_populates="events")
    notification_id: int | None = Field(
        default=None,
        foreign_key="notification.id",
        ondelete="CASCADE"
    )
    notification: "Notification" = Relationship(back_populates="events")

class NotificationType(enum.Enum):
    task_start = "task_start"
    task_end = "task_end"
    other = "other"

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
    type: NotificationType = Field(default=NotificationType.other)

    # User that created the notification
    owner_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="created_notifications")

    events: list[Event] = Relationship(
        back_populates="notification",
        cascade_delete=True
    )
    receivers_users: list[User] = Relationship(
        back_populates="notifications",
        link_model=UserHasNotification
    )
    receivers_groups: list[Group] = Relationship(
        back_populates="notifications",
        link_model=GroupHasNotification
    )

# TODO - add automatic reaction to events?

class Limit(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str | None = None
    amount: int

    # Either user or group must be set
    user_id: int | None = Field(
        default=None,
        foreign_key="user.id",
        ondelete="CASCADE"
    )
    user: User | None = Relationship(back_populates="limits")
    group_id: int | None = Field(
        default=None,
        foreign_key="group.id",
        ondelete="CASCADE"
    )
    group: Group | None = Relationship(back_populates="limits")

    resource_id: int = Field(
        default=None,
        foreign_key="resource.id",
        ondelete="CASCADE"
    )
    resource: Resource = Relationship(back_populates="limits")
    nodes: list[Node] = Relationship(
        back_populates="limits",
        link_model=NodeIsLimitedBy
    )
