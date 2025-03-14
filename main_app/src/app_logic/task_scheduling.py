from sqlalchemy.orm import Session
from src.db.models import User, Task, TaskStatus, Event
from datetime import datetime, timedelta

    

def add_curent_task_alerts(user: User, db_session: Session) -> None:
    """
    Adds current task alerts to Grafana.
    """
    time_trashold = datetime.now()
    # get current tasks for given user
    tasks = db_session.query(Task).filter(
        Task.status.in_([TaskStatus.running, TaskStatus.scheduled]),
        Task.owner_id == user.id,
        Task.start_time <= time_trashold + timedelta(minutes=1)
    ).all()

    required_resources = {}

    for task in tasks:
        for ra in task.resource_allocations:
            if ra.node_id not in required_resources:
                required_resources[ra.node_id] = {}
            if ra.resource_id not in required_resources[ra.node_id]:
                required_resources[ra.node_id][ra.resource_id] = ra.amount
            else:
                required_resources[ra.node_id][ra.resource_id] += ra.amount

    # TODO - change alert configuration according to required resources

    # TODO - remove start / end events for task and change task status to
    # running / ended
