from sqlalchemy.orm import Session
from src.db.models import User, Task, TaskStatus, Event
from datetime import datetime, timedelta
from src.app_logic.notification_operations import (
    grafana_update_user_alerts_on_task_event
)


# TODO - add task scheduling when event begins
# TODO - add table locking to relevant functions
# TODO - add task dashboard to Grafana when started
