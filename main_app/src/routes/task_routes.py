from fastapi import APIRouter
from src.app_logic.task_operations import (
    get_all_tasks,
    get_task,
    schedule_task,
    remove_task,
    add_tag_to_task,
    remove_tag_from_task
)
from src.db.models import Task, TaskHasTag
from src.schemas.task_entities import (
    TaskResponseSimple,
    TaskResponseFull,
    CreateTaskRequest
)
from . import SessionDep

task_route = APIRouter(
    prefix="/task"
)

# TODO - AUTH - add authentication and pass user id to operations

@task_route.get("/", response_model=list[TaskResponseSimple])
def get_tasks(session: SessionDep) -> list[TaskResponseSimple]:
    """
    Returns all tasks.
    """
    return get_all_tasks(db_session=session)

@task_route.get("/{task_id}", response_model=TaskResponseFull)
def task_get(task_id: int, session: SessionDep) -> TaskResponseFull:
    """
    Returns task by id
    """
    return get_task(task_id=task_id, db_session=session)

@task_route.post("/", response_model=TaskResponseFull)
def task_create(
    task: CreateTaskRequest,
    session: SessionDep
) -> TaskResponseFull:
    """
    Creates new task or updates existing one.
    """
    # TODO - AUTH - change owner ID to current user!
    return schedule_task(task=task, owner_id=1, db_session=session)

@task_route.delete("/{task_id}", status_code=200, response_model=dict)
def task_delete(task_id: int, session: SessionDep) -> None:
    """
    Deletes task.
    """
    remove_task(task_id=task_id, db_session=session)
    return {'detail': 'Task deleted'}

@task_route.post("/add_tag", response_model=TaskResponseFull)
def task_add_tag(
    task_tag_request: TaskHasTag,
    session: SessionDep
) -> TaskResponseFull:
    """
    Adds tag to task
    """
    # TODO - AUTH - add user id
    return add_tag_to_task(
        task_tag_request=task_tag_request,
        user_id=1,
        db_session=session
    )

@task_route.post("/remove_tag", response_model=TaskResponseFull)
def task_remove_tag(
    task_tag_request: TaskHasTag,
    session: SessionDep
) -> TaskResponseFull:
    """
    Removes tag from task
    """
    # TODO - AUTH - add user id
    return remove_tag_from_task(
        task_tag_request=task_tag_request,
        user_id=1,
        db_session=session
    )
