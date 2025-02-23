from fastapi import APIRouter
from src.app_logic.task_tag_operations import (
    get_user_tags,
    get_group_tags,
    get_all_tags,
    get_tag,
    create_tag,
    update_tag,
    delete_tag
)
from src.db.models import TaskTag
from src.schemas.task_tag_entities import TaskTagResponse
from src.app_logic.authentication import ensure_admin_permissions
from . import SessionDep, LoginDep

task_tag_route = APIRouter(
    prefix="/task_tag"
)

@task_tag_route.get("/", response_model=list[TaskTagResponse])
def get_all_task_tags(
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskTagResponse]:
    """
    Returns all task tags.
    """
    ensure_admin_permissions(current_user=current_user)
    return get_all_tags(db_session=session)

@task_tag_route.get("/user/{user_id}", response_model=list[TaskTagResponse])
def get_user_task_tags(
    user_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskTagResponse]:
    """
    Returns task tags by user id.
    """
    return get_user_tags(
        user_id=user_id,
        current_user=current_user,
        db_session=session
    )

@task_tag_route.get("/group/{group_id}", response_model=list[TaskTagResponse])
def get_group_task_tags(
    group_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> list[TaskTagResponse]:
    """
    Returns task tags by group id.
    """
    return get_group_tags(
        group_id=group_id,
        current_user=current_user,
        db_session=session
    )

@task_tag_route.get("/{task_tag_id}", response_model=TaskTagResponse)
def task_tag_get(
    task_tag_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> TaskTagResponse:
    """
    Returns task tag by id.
    """
    return get_tag(
        tag_id=task_tag_id,
        current_user=current_user,
        db_session=session
    )

@task_tag_route.post("/", response_model=TaskTagResponse)
def task_tag_create(
    task_tag: TaskTag,
    current_user: LoginDep,
    session: SessionDep
) -> TaskTagResponse:
    """
    Creates new task tag.
    """
    return create_tag(
        tag=task_tag,
        current_user=current_user,
        db_session=session
    )

@task_tag_route.put("/", response_model=TaskTagResponse)
def task_tag_update(
    task_tag: TaskTag,
    current_user: LoginDep,
    session: SessionDep
) -> TaskTagResponse:
    """
    Updates task tag.
    """
    return update_tag(
        tag=task_tag,
        current_user=current_user,
        db_session=session
    )

@task_tag_route.delete("/{task_tag_id}", response_model=dict)
def task_tag_delete(
    task_tag_id: int,
    current_user: LoginDep,
    session: SessionDep
) -> dict:
    """
    Deletes task tag.
    """
    delete_tag(
        tag_id=task_tag_id,
        current_user=current_user,
        db_session=session
    )
    return {'detail': 'Task tag deleted'}
