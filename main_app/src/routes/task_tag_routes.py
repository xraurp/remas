from fastapi import APIRouter
from src.app_logic.task_tag_operations import (
    get_user_tags,
    get_tag,
    create_tag,
    update_tag,
    delete_tag
)
from src.db.models import TaskTag
from src.schemas.task_tag_entities import TaskTagResponse
from . import SessionDep

task_tag_route = APIRouter(
    prefix="/task_tag"
)

@task_tag_route.get("/", response_model=list[TaskTagResponse])
def get_user_task_tags(session: SessionDep) -> list[TaskTagResponse]:
    """
    Returns all task tags.
    """
    # TODO - AUTH - add user id
    return get_user_tags(user_id=1, db_session=session)

@task_tag_route.get("/{task_tag_id}", response_model=TaskTagResponse)
def task_tag_get(task_tag_id: int, session: SessionDep) -> TaskTagResponse:
    """
    Returns task tag by id.
    """
    # TODO - AUTH - add user id
    return get_tag(tag_id=task_tag_id, user_id=1, db_session=session)

@task_tag_route.post("/", response_model=TaskTagResponse)
def task_tag_create(task_tag: TaskTag, session: SessionDep) -> TaskTagResponse:
    """
    Creates new task tag.
    """
    # TODO - AUTH - add user id
    return create_tag(tag=task_tag, user_id=1, db_session=session)

@task_tag_route.put("/", response_model=TaskTagResponse)
def task_tag_update(task_tag: TaskTag, session: SessionDep) -> TaskTagResponse:
    """
    Updates task tag.
    """
    # TODO - AUTH - add user id
    return update_tag(tag=task_tag, user_id=1, db_session=session)

@task_tag_route.delete("/{task_tag_id}", response_model=dict)
def task_tag_delete(task_tag_id: int, session: SessionDep) -> dict:
    """
    Deletes task tag.
    """
    # TODO - AUTH - add user id
    try:
        delete_tag(tag_id=task_tag_id, user_id=1, db_session=session)
        return {'detail': 'Task tag deleted'}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
