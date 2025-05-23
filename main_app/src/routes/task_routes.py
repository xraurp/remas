from fastapi import APIRouter
from src.app_logic.task_operations import (
    get_all_tasks,
    get_task,
    schedule_task,
    remove_task,
    add_tag_to_task,
    remove_tag_from_task,
    get_user_tasks,
    get_resource_availability_schedule,
    get_active_tasks,
    get_finished_tasks,
    get_active_tasks_for_user,
    get_finished_tasks_for_user
)
from src.db.models import Task, TaskHasTag
from src.schemas.task_entities import (
    TaskResponseSimple,
    TaskResponseFull,
    CreateTaskRequest,
    UsagePeriod,
    ResourceScheduleRequest,
    TaskResponseFullWithOwner,
    TasksPaginationRequest
)
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

task_route = APIRouter(
    prefix="/task"
)


@task_route.get("", response_model=list[TaskResponseSimple])
def get_tasks(
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseSimple]:
    """
    Returns all tasks.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_tasks(db_session=session)

@task_route.get("/user/{user_id}", response_model=list[TaskResponseSimple])
def tasks_get_by_user(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseSimple]:
    """
    Returns tasks owned by user.
    """
    return get_user_tasks(
        user_id=user_id,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/user/{user_id}/active", response_model=list[TaskResponseFull])
def tasks_get_active_by_user(
    user_id: int,
    pagination: TasksPaginationRequest,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseFull]:
    """
    Returns active tasks owned by user.
    """
    return get_active_tasks_for_user(
        user_id=user_id,
        pagination=pagination,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/user/{user_id}/finished", response_model=list[TaskResponseFull])
def tasks_get_finished_by_user(
    user_id: int,
    pagination: TasksPaginationRequest,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseFull]:
    """
    Returns finished tasks owned by user.
    """
    print('user_id', user_id)
    return get_finished_tasks_for_user(
        user_id=user_id,
        pagination=pagination,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/finished", response_model=list[TaskResponseFullWithOwner])
def tasks_get_finished(
    pagination: TasksPaginationRequest,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseFull]:
    """
    Returns finished tasks owned by user.
    """
    return get_finished_tasks(
        pagination=pagination,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/active", response_model=list[TaskResponseFullWithOwner])
def tasks_get_active(
    pagination: TasksPaginationRequest,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskResponseFull]:
    """
    Returns active tasks owned by user.
    """
    return get_active_tasks(
        pagination=pagination,
        current_user=current_user,
        db_session=session
    )

@task_route.get("/{task_id}", response_model=TaskResponseFull)
def task_get(
    task_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> TaskResponseFull:
    """
    Returns task by id
    """
    return get_task(
        task_id=task_id,
        current_user=current_user,
        db_session=session
    )

@task_route.post("", response_model=TaskResponseFull)
def task_create(
    task: CreateTaskRequest,
    current_user: LoginDep,
    session: SessionDep
) -> TaskResponseFull:
    """
    Creates new task or updates existing one.
    """
    return schedule_task(
        task=task,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/get_scheduling", response_model=list[UsagePeriod])
def get_scheduling(
    request: ResourceScheduleRequest,
    current_user: LoginDep,
    session: SessionDep
) -> list[UsagePeriod]:
    """
    Creates new task or updates existing one.
    """
    return get_resource_availability_schedule(
        request=request,
        db_session=session
    )

@task_route.delete("/{task_id}", status_code=200, response_model=dict)
def task_delete(
    task_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> None:
    """
    Deletes task.
    """
    remove_task(
        task_id=task_id,
        current_user=current_user,
        db_session=session
    )
    return {'detail': 'Task deleted'}

@task_route.post("/add_tag", response_model=TaskResponseFull)
def task_add_tag(
    task_tag_request: TaskHasTag,
    current_user: LoginDep,
    session: SessionDep
) -> TaskResponseFull:
    """
    Adds tag to task
    """
    return add_tag_to_task(
        task_tag_request=task_tag_request,
        current_user=current_user,
        db_session=session
    )

@task_route.post("/remove_tag", response_model=TaskResponseFull)
def task_remove_tag(
    task_tag_request: TaskHasTag,
    current_user: LoginDep,
    session: SessionDep
) -> TaskResponseFull:
    """
    Removes tag from task
    """
    return remove_tag_from_task(
        task_tag_request=task_tag_request,
        current_user=current_user,
        db_session=session
    )
