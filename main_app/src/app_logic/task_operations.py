from src.db.models import (
    Task,
    ResourceAllocation,
    EventType,
    Event,
    Node,
    TaskStatus,
    TaskTag,
    TaskHasTag,
    Limit,
    User
)
from sqlmodel import select, Session
from sqlalchemy.exc import IntegrityError
from src.schemas.task_entities import (
    TaskResponseFull,
    TaskResourceAllocationResponse,
    TaskResponseSimple,
    TaskResponseFullWithOwner,
    CreateTaskRequest,
    ResourceAllocationRequest,
)
from src.schemas.user_entities import UserNoPasswordSimple
from src.app_logic.limit_operations import get_all_user_limits_dict
from src.app_logic.notification_operations import (
    get_notifications_by_user_id,
    schedule_notification_events_for_task
)
from src.app_logic.authentication import insufficientPermissionsException
from src.schemas.authentication_entities import CurrentUserInfo
from fastapi import HTTPException
from datetime import datetime

# TODO - add selecting by tag
# TODO - add get statistics by tag and share resources in groups

def generate_task_response_full(task: Task) -> TaskResponseFull:
    return TaskResponseFull(
        id=task.id,
        name=task.name,
        description=task.description,
        start_time=task.start_time,
        end_time=task.end_time,
        status=task.status,
        tags=task.tags,
        resources=[
            TaskResourceAllocationResponse(
                node=resource_allocation.node,
                resource=resource_allocation.resource,
                amount=resource_allocation.amount
            )
            for resource_allocation in task.resource_allocations
        ],
    )

def generate_task_response_full_with_owner(
    task: Task
) -> TaskResponseFullWithOwner:
    task_response = generate_task_response_full(task=task)
    task_response_wtih_owner = TaskResponseFullWithOwner(
        owner=UserNoPasswordSimple(**task.owner.model_dump()),
        **task_response.model_dump()
    )
    return task_response_wtih_owner

def generate_task_response_simple(task: Task) -> TaskResponseSimple:
    return TaskResponseSimple(
        id=task.id,
        name=task.name,
        description=task.description,
        start_time=task.start_time,
        end_time=task.end_time,
        status=task.status,
        owner=UserNoPasswordSimple(**task.owner.model_dump())
    )

def get_all_tasks(db_session: Session) -> list[TaskResponseSimple]:
    """
    Returns all tasks.
    """
    return [
        generate_task_response_simple(task=task)
        for task in db_session.scalars(select(Task)).all()
    ]

def get_user_tasks(
    user_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> list[TaskResponseSimple]:
    """
    Returns tasks owned by specified user.
    """
    if not current_user.is_admin:
        if current_user.user_id != user_id:
            raise insufficientPermissionsException
    return [
        generate_task_response_simple(task=task)
        for task in db_session.scalars(
            select(Task).where(Task.owner_id == user_id)
        ).all()
    ]

def get_task(
    task_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> TaskResponseFull:
    """
    Returns task by id
    """
    task = db_session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found!"
        )
    user = db_session.get(User, current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {current_user.user_id} not found!"
        )
    if not current_user.is_admin:
        if current_user.user_id != task.owner_id:
            if user.group_id != task.owner.group_id \
            or not user.group.users_share_statistics:
                raise insufficientPermissionsException
    return generate_task_response_full(task=task)


# TASK SCHEDULING
def modify_required_resources(
    required_nodes_resources: dict[int, dict[int, int]],
    task: Task,
    add: bool
) -> None:
    """
    Adds/removes required resources for overlaping tasks.
    Modifies data in place.
    :param required_nodes_resources (dict[int, dict[int, int]]): dictionary of
        required nodes and resources
    :param task (Task): task to add / remove
    :param add (bool): whether to add (True) or remove (False)
    """
    for ra in task.resource_allocations:
        if ra.node_id not in required_nodes_resources:
            continue
        if ra.resource_id not in required_nodes_resources[ra.node_id]:
            continue
        if add:
            required_nodes_resources[ra.node_id][ra.resource_id] += ra.amount
        else:
            required_nodes_resources[ra.node_id][ra.resource_id] -= ra.amount

def check_resource_availability(
    required_nodes_resources: dict[int, dict[int, int]],
    node_resources: dict[int, dict[int, int]]
):
    """
    Checks if there is enough resources for the task.
    """
    for node_id, resources in required_nodes_resources.items():
        for resource_id, amount in resources.items():
            if node_resources[node_id][resource_id] < amount:
                return False
    return True

def taskrequest_to_task(
    task: CreateTaskRequest,
    owner_id: int,
    db_session: Session
) -> Task:
    """
    Generates task from task request.
    :param task (CreateTaskRequest): task request with task data
    :param owner_id (int): id of the task owner
    :param db_session (Session): database session to use
    :return (Task): New task that can be added to database
    """
    task_to_schedule = Task(
        id=task.id,
        name=task.name,
        description=task.description,
        start_time=task.start_time,
        end_time=task.end_time,
        status=TaskStatus.scheduled,
        owner_id=owner_id,
        resource_allocations=[
            ResourceAllocation(
                node_id=task_ra.node_id,
                resource_id=task_ra.resource_id,
                amount=task_ra.amount
            )
            for task_ra in task.resource_allocations
        ],
        events = [
            Event(
                name=f"{task.name} start",
                description=f"Start of {task.name}",
                time=task.start_time,
                type=EventType.task_start,
            ),
            Event(
                name=f"{task.name} end",
                description=f"End of {task.name}",
                time=task.end_time,
                type=EventType.task_end,
            )
        ]
    )
    db_session.add(task_to_schedule)
    return task_to_schedule

def check_resource_changes(
    task_request: CreateTaskRequest,
    existing_task: Task
) -> bool:
    """
    Checks if resource allocation has changed in the request.
    :param task_request (CreateTaskRequest): task request
    :param existing_task (Task): existing task in database
    :return (bool): True if allocation has changed, else False
    """
    new_resources = [
        ResourceAllocation(
            task_id = task_request.id,
            node_id = task_ra.node_id,
            resource_id = task_ra.resource_id,
            amount = task_ra.amount
        )
        for task_ra in task_request.resource_allocations
    ]
    for ra in new_resources:
        if ra not in existing_task.resource_allocations:
            return True
    for ra in existing_task.resource_allocations:
        if ra not in new_resources:
            return True
    return False

def update_task_info_from_request(
    task_request: CreateTaskRequest,
    existing_task: Task
) -> None:
    """
    Updates tasks information from task request.
    :param task_request (CreateTaskRequest): task request
    :param existing_task (Task): existing task in database
    """
    existing_task.name = task_request.name
    existing_task.description = task_request.description

def update_task_scheduling_from_request(
    task_request: CreateTaskRequest,
    existing_task: Task
) -> None:
    """
    Updates start and end time of task from task request.
    :param task_request (CreateTaskRequest): task request
    :param existing_task (Task): existing task in database
    """
    if existing_task.status == TaskStatus.finished:
        raise HTTPException(
            status_code=409,
            detail="Task scheduling time cannot be updated after"
                   " task has finished!"
        )
    if existing_task.status == TaskStatus.running \
    and existing_task.start_time != task_request.start_time:
        raise HTTPException(
            status_code=409,
            detail="Task start time cannot be changed if task"
                    " has already started!"
        )
    
    existing_task.start_time = task_request.start_time
    existing_task.end_time = task_request.end_time
    now = datetime.now()
    for e in existing_task.events:
        if e.type == EventType.task_start:
            e.time = task_request.start_time
        if e.type == EventType.task_end:
            e.time = task_request.end_time
    
    # TODO - change scheduling of the notifications connected to start/end of
    #        the task

def check_user_limit(
    user_limits: dict[int, dict[int, Limit]],
    required_nodes_resources: dict[int, dict[int, int]]
) -> None:
    """
    Check if user is not restricted from using required resources.
    :param user_limits (dict[int, dict[int, Limit]]): user limits by resource
    :param required_nodes_resources (dict[int, dict[int, int]]): required
        resources
    :raises HTTPException: if user is restricted
    """
    for node_id, resources in required_nodes_resources.items():
        for resource_id, amount in resources.items():
            try:  # check if resource is limited, if not, continue
                limit_amount = user_limits[resource_id][node_id].amount
            except KeyError:
                continue
            if limit_amount < amount:
                raise HTTPException(
                    status_code=409,
                    detail="Task resource allocation exeeds user limits!"
                           " Exceeded resource: "
                           f"{user_limits[resource_id][node_id].name}, Limit: "
                           f"{user_limits[resource_id][node_id].amount}"
                )


def update_task_resources_from_request(
    task_request: CreateTaskRequest,
    existing_task: Task
) -> None:
    """
    Updates resources of existing task from task request.
    :param task_request (CreateTaskRequest): task request
    :param existing_task (Task): existing task in database
    """
    new_resources = [
        ResourceAllocation(
            task_id = task_request.id,
            node_id = task_ra.node_id,
            resource_id = task_ra.resource_id,
            amount = task_ra.amount
        )
        for task_ra in task_request.resource_allocations
    ]
    existing_task.resource_allocations = new_resources

def update_task_from_request(
    task_request: CreateTaskRequest,
    existing_task: Task
) -> None:
    """
    Updates task data from task request.
    :param task_request (CreateTaskRequest): task request
    :param existing_task (Task): existing task in database
    """
    update_task_info_from_request(
        task_request=task_request,
        existing_task=existing_task
    )
    update_task_resources_from_request(
        task_request=task_request,
        existing_task=existing_task
    )
    update_task_scheduling_from_request(
        task_request=task_request,
        existing_task=existing_task
    )

def reschedule_task_notifications(
    task: Task,
    current_user: CurrentUserInfo,
    db_session: Session
) -> None:
    """
    Reschedules notifications for task.
    :param task (Task): task to reschedule
    :param current_user (CurrentUserInfo): currently logged in user information
    :param db_session (Session): database session
    """
    # TODO - add current user data
    notifications = get_notifications_by_user_id(
        user_id=current_user.user_id,
        current_user=current_user,
        db_session=db_session
    )
    for grop_notifications in notifications:
        for notification in grop_notifications.notifications:
            schedule_notification_events_for_task(
                notification=notification,
                task=task,
                db_session=db_session
            )

def schedule_task(
    task: CreateTaskRequest,
    current_user: CurrentUserInfo,
    db_session: Session
) -> TaskResponseFull:
    """
    Adds task or updates existing one.
    :param task (CreateTaskRequest): task to schedule
    :param current_user (CurrentUserInfo): currently logged in user information
    :param db_session (Session): database session
    :return (TaskResponse): scheduled task
    """
    if not task.resource_allocations:
        raise HTTPException(
            status_code=400,
            detail="Task must have at least one resource allocation!"
        )
    if task.start_time >= task.end_time:
        raise HTTPException(
            status_code=400,
            detail="Task start time must be before its end time!"
        )
    
    # TODO - lock the task table while scheduling
    # Check if existing task is being updated
    if task.id:
        existing_task = db_session.get(Task, task.id)
        if not existing_task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with id {task.id} not found!"
            )
        if existing_task.owner_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Task is not owned by current user!"
            )
        
        # Update task info if rescheduling is not needed
        if existing_task.start_time == task.start_time \
        and existing_task.end_time == task.end_time \
        and not check_resource_changes(
            task_request=task,
            existing_task=existing_task
        ):
            update_task_info_from_request(
                task_request=task,
                existing_task=existing_task
            )
            db_session.commit()
            db_session.refresh(existing_task)
            return existing_task
    else:
        existing_task = None

    # Create structure of required nodes and resources
    # {
    #     node_id: {
    #         resource_id: amount
    #     }
    # }
    required_nodes_resources = {}
    node_resources = {}
    for task_ra in task.resource_allocations:
        if task_ra.node_id not in required_nodes_resources:
            required_nodes_resources[task_ra.node_id] = {}
        if task_ra.node_id not in node_resources:
            node_resources[task_ra.node_id] = {}
        required_nodes_resources[task_ra.node_id][task_ra.resource_id] = \
            task_ra.amount
        node_resources[task_ra.node_id][task_ra.resource_id] = None
    
    # Check if resource allocation does not exeeds limits
    user_limits = get_all_user_limits_dict(
        user_id=current_user.user_id,
        session=db_session
    )
    check_user_limit(
        user_limits=user_limits,
        required_nodes_resources=required_nodes_resources
    )

    # Get all nodes that are required for the task
    nodes = db_session.scalars(
        select(Node).where(
            Node.id.in_(
                [task_ra.node_id for task_ra in task.resource_allocations]
            )
        )
    ).all()

    # Get amount of each required resource provided by the node
    for node in nodes:
        for resource in node.resources:
            if resource.resource_id in required_nodes_resources[node.id]:
                node_resources[node.id][resource.resource_id] = resource.amount
    
    # Find overlapping tasks (excluding current task)
    overlapping_tasks = db_session.scalars(
        select(Task).where(
            Task.status.in_([TaskStatus.scheduled, TaskStatus.running]),
            Task.start_time <= task.end_time,
            Task.end_time >= task.start_time
        ).where(
            Task.id != (existing_task.id if existing_task else None)
        ).order_by(Task.start_time)
    ).all()
    overlap_ends = [o for o in overlapping_tasks]
    overlap_ends.sort(key=lambda o: o.end_time)

    # Check if there are enough resources for the task
    for t in overlapping_tasks:
        # if some of the overlapping tasks ends, check if there are enough
        # resources for all the currently scheduled tasks
        if len(overlap_ends) and t.start_time >= overlap_ends[0].end_time:
            if not check_resource_availability(
                required_nodes_resources=required_nodes_resources,
                node_resources=node_resources
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Not enough resources for the task!"
                )
        # subtract resources from all the overlapping tasks that ends before
        # current task starts
        while len(overlap_ends) and t.start_time >= overlap_ends[0].end_time:
            modify_required_resources(
                required_nodes_resources=required_nodes_resources,
                task=overlap_ends[0],
                add=False
            )
            overlap_ends.pop(0)
        # add resources from the starting overlapping task to the required
        # resources
        modify_required_resources(
            required_nodes_resources=required_nodes_resources,
            task=t,
            add=True
        )
    
    # Check for resource availability at last overlapping time section with
    # other tasks
    if not check_resource_availability(
        required_nodes_resources=required_nodes_resources,
        node_resources=node_resources
    ):
        raise HTTPException(
            status_code=409,
            detail="Not enough resources for the task!"
        )
    
    # Schedule task
    if existing_task:
        update_task_from_request(
            task_request=task,
            existing_task=existing_task
        )
    else:
        existing_task = taskrequest_to_task(
            task=task,
            owner_id=current_user.user_id,
            db_session=db_session
        )
    try:
        db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Task with the same name already exists!"
        )
    
    # reschedule task notifications
    db_session.refresh(existing_task)
    reschedule_task_notifications(
        task=existing_task,
        current_user=current_user,
        db_session=db_session
    )
    db_session.commit()
    # TODO - unlock the task table after scheduling

    db_session.refresh(existing_task)
    return generate_task_response_full(task=existing_task)

def remove_task(
    task_id: int,
    current_user: CurrentUserInfo,
    db_session: Session
) -> None:
    """
    Removes task
    """
    task = db_session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found!"
        )
    if task.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Can't remove task owned by another user!"
        )
    db_session.delete(task)
    db_session.commit()

def add_tag_to_task(
    task_tag_request: TaskHasTag,
    current_user: CurrentUserInfo,
    db_session: Session
) -> Task:
    """
    Adds tag to task
    """
    tag = db_session.get(TaskTag, task_tag_request.tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {task_tag_request.tag_id} not found!"
        )
    if tag.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't add tag owned by another user!"
        )
    task = db_session.get(Task, task_tag_request.task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_tag_request.task_id} not found!"
        )
    if task.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Can't add tag to task owned by another user!"
        )
    if tag not in task.tags:
        task.tags.append(tag)
        db_session.commit()
        db_session.refresh(task)
        return generate_task_response_full(task=task)
    else:
        raise HTTPException(
            status_code=409,
            detail="Tag is already assigned to the task!"
        )

def remove_tag_from_task(
    task_tag_request: TaskHasTag,
    current_user: CurrentUserInfo,
    db_session: Session
) -> Task:
    """
    Removes tag from task
    """
    tag = db_session.get(TaskTag, task_tag_request.tag_id)
    if not tag:
        raise HTTPException(
            status_code=404,
            detail=f"Tag with id {task_tag_request.tag_id} not found!"
        )
    if tag.user_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail=f"Can't remove tag owned by another user!"
        )
    task = db_session.get(Task, task_tag_request.task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_tag_request.task_id} not found!"
        )
    if task.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Can't remove tag from task owned by another user!"
        )
    if tag in task.tags:
        task.tags.remove(tag)
        db_session.commit()
        db_session.refresh(task)
        return generate_task_response_full(task=task)
    else:
        raise HTTPException(
            status_code=404,
            detail="Tag is not assigned to the task!"
        )
