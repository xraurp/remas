from src.db.models import (
    Task,
    ResourceAllocation,
    EventType,
    Event,
    Node,
    TaskStatus
)
from sqlmodel import select, Session
from src.schemas.task_entities import (
    TaskResponseFull,
    TaskResourceAllocationResponse,
    TaskResponseSimple,
    TaskResponseFullWithOwner,
    CreateTaskRequest,
    ResourceAllocationRequest,
)
from src.schemas.user_entities import UserNoPasswordSimple
from fastapi import HTTPException

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

def get_task(task_id: int, db_session: Session) -> TaskResponseFull:
    """
    Returns task by id
    """
    return generate_task_response_full(task=db_session.get(Task, task_id))


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

def schedule_task(
    task: CreateTaskRequest,
    owner_id: int,
    db_session: Session
) -> TaskResponseFull:
    """
    Adds task
    :param task (CreateTaskRequest): task to schedule
    :param owner_id (int): id of task owner
    :param db_session (Session): database session
    :return (TaskResponse): scheduled task
    """
    # TODO - add functionality toupdate task
    if not task.resource_allocations:
        raise HTTPException(
            status_code=400,
            detail="Task must have at least one resource allocation!"
        )
    if task.start_time >= task.end_time:
        raise ValueError(
            status_code=400,
            detail="Task start time must be before its end time!"
        )
    
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
    
    # TODO - lock the task table while scheduling
    # Find overlapping tasks
    overlapping_tasks = db_session.scalars(
        select(Task).where(
            Task.status.in_([TaskStatus.scheduled, TaskStatus.running]),
            Task.start_time <= task.end_time,
            Task.end_time >= task.start_time
        ).order_by(Task.start_time)
    ).all()
    overlap_ends = [o for o in overlapping_tasks]
    overlap_ends.sort(key=lambda o: o.end_time)
    print(overlapping_tasks)
    print(overlap_ends)

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
    task_to_schedule = Task(
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
    db_session.commit()
    # TODO - unlock the task table after scheduling
    # TODO - add notifications according to user configuration
    return generate_task_response_full(task=task_to_schedule)

def remove_task(task_id: int, db_session: Session) -> None:
    """
    Removes task
    """
    task = db_session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found!"
        )
    db_session.delete(task)
    db_session.commit()
