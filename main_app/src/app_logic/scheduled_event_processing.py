from sqlalchemy.orm import Session
from src.db.models import User, Task, TaskStatus, Event, EventType
from datetime import datetime, timedelta
from src.config import get_settings
from src.app_logic.grafana_alert_operations import (
    grafana_add_or_update_user_alerts
)
import redmail
from string import Template
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from src.db.connection import get_db_engine
import smtplib
import traceback


# TODO - add task dashboard to Grafana when task is started

SCHEDULER = None
JOB_ID = 'process_events'

def init_scheduler() -> None:
    global SCHEDULER
    SCHEDULER = BackgroundScheduler()
    schedule_next_event_processing(get_db_session_for_scheduler())
    SCHEDULER.start()

def shutdown_scheduler() -> None:
    global SCHEDULER
    SCHEDULER.shutdown()

def get_db_session_for_scheduler() -> Session:
    """
    Returns database session.
    In scheduler, dependency injection does not work,
    so the src.db.connection.get_session() cannot be used.
    """
    return Session(bind=get_db_engine())

def log_event_info(event: Event, content: str) -> None:
    """
    Logs event information.
    :param event (Event): event to log
    :param content (str): notification content
    """
    logging.info(
        f"Notification: {event.notification.name}, "
        f"Receiver: {event.task.owner.email}"
    )
    logging.debug(
        f"Notification content: {content}"
    )

def send_notification_on_event(event: Event) -> None:
    """
    Sends notification to user when event triggers it:
    :param event (Event): event to send notification for
    """
    content = Template(
        event.notification.notification_template
    ).safe_substitute(
        user_id=event.task.owner.id,
        user_name=event.task.owner.name,
        user_surname=event.task.owner.surname,
        user_username=event.task.owner.username,
        user_uid=event.task.owner.uid,
        user_email=event.task.owner.email,
        task_id=event.task.id,
        task_name=event.task.name,
        task_description=event.task.description,
        task_start=event.task.start_time,
        task_end=event.task.end_time
    )
    if get_settings().smtp_enabled \
    and not (
                get_settings().smtp_user and
                get_settings().smtp_password and
                get_settings().smtp_from_address
            ):
        logging.error(
            "SMTP is enabled, but SMTP_USER, SMTP_PASSWORD "
            "or SMTP_FROM_ADDRESS is not set! "
            "Notification will not be sent!"
        )
    elif get_settings().smtp_enabled:
        if get_settings().smtp_starttls_enabled:
            cls_smtp = smtplib.SMTP
        else:
            cls_smtp = smtplib.SMTP_SSL
        try:
            mailsender = redmail.EmailSender(
                host=get_settings().smtp_host,
                port=get_settings().smtp_port,
                username=get_settings().smtp_user,
                password=get_settings().smtp_password,
                use_starttls=get_settings().smtp_starttls_enabled,
                cls_smtp=cls_smtp
            )
            mailsender.send(
                sender=f'{get_settings().smtp_from_name} '
                    f'<{get_settings().smtp_from_address}>',
                receivers=[event.task.owner.email],
                subject=event.notification.name,
                text=content
            )
        except Exception as e:
            logging.error(
                f"Error sending notification {event.notification.name} "
                f"to {event.task.owner.email}!"
            )
            logging.error(traceback.format_exc())
    else:
        logging.warning(
            "SMTP is not enabled, notification will not be sent!"
        )
    
    log_event_info(event=event, content=content)

def process_scheduled_events(db_session: Session) -> None:
    """
    Processes scheduled events
    """
    timepoint = datetime.now() + timedelta(
        seconds=get_settings().task_scheduler_precision_seconds
    )

    logging.debug(f"Processing scheduled events at {timepoint}")

    # get events from database within time window
    events = db_session.query(Event).with_for_update().filter(
        Event.time <= timepoint
    ).order_by(
        Event.time
    ).all()

    # list of users that needs change of alerts in grafana
    afected_users = []
    # list of events that were processed and can be removed from database
    processed_events = []

    for event in events:
        savepoint = db_session.begin_nested()

        # event is task start or task end
        if event.type in [EventType.task_start, EventType.task_end]:
            # update task status
            task = event.task
            if event.type == EventType.task_start \
            and task.start_time <= timepoint: # check if task wasn't rescheduled
                task.status = TaskStatus.running
                if task.owner not in afected_users:
                    afected_users.append(task.owner)
                processed_events.append(event)
            elif event.type == EventType.task_end \
            and task.end_time <= timepoint: # check if task wasn't rescheduled
                task.status = TaskStatus.finished
                if task.owner not in afected_users:
                    afected_users.append(task.owner)
                processed_events.append(event)
        
        # user notification event
        elif event.type == EventType.other:
            # send notification
            send_notification_on_event(event=event)
            
            # remove event after processing
            db_session.delete(event)
        savepoint.commit()

    for user in afected_users:
        savepoint = db_session.begin_nested()

        # update grafana alerts for afected users (task owners)
        errors = grafana_add_or_update_user_alerts(
            user=user,
            timepoint=timepoint,
            db_session=db_session,
            lock_rows=True
        )

        if errors:
            logging.error(
                f"Errors has occured when updating"
                f" grafana alerts for user {user.username}!"
            )

        # remove events for afected users after alerts have been updated
        for event in processed_events:
            if event.task.owner == user:
                db_session.delete(event)
            
        savepoint.commit()
    
    db_session.commit()

def process_scheduled_events_scheduler_job() -> None:
    """
    Function called by the scheduler when events need to be processed.
    """
    db_session = get_db_session_for_scheduler()
    try:
        process_scheduled_events(db_session=db_session)
    except Exception as e:
        logging.error(f"Error processing scheduled events: {e}")
        logging.debug(traceback.format_exc())
        schedule_next_event_processing(
            db_session=db_session,
            retry=True
        )
    else:
        schedule_next_event_processing(db_session=db_session)
    db_session.close()

def schedule_next_event_processing(
    db_session: Session,
    retry: bool = False,
) -> None:
    """
    Schedules next event processing
    :param db_session (Session): database session
    :param retry (bool): whether to retry processing
        in seconds
    """
    global SCHEDULER
    global JOB_ID

    if retry:
        timepoint = datetime.now() + timedelta(
            seconds=get_settings().task_scheduler_retry_limit_seconds
        )
    else:
        try:
            next_event = db_session.query(Event).order_by(Event.time).first()
        except Exception as e:
            logging.error(f"Error getting next event: {e}")
            logging.debug(traceback.format_exc())
            timepoint = datetime.now() + timedelta(
                seconds=get_settings().task_scheduler_retry_limit_seconds
            )
        else:
            if not next_event:
                return

            timepoint = next_event.time

            if timepoint < datetime.now() + timedelta(seconds=10):
                timepoint = datetime.now() + timedelta(seconds=10)
    
    # add next job scheduling
    try:
        SCHEDULER.add_job(
            func=process_scheduled_events_scheduler_job,
            next_run_time=timepoint,
            id=JOB_ID
        )
    except ConflictingIdError:
        # job is already scheduled
        # (could be due to race condition or scheduler and API process)
        cancel_next_event_processing()
        schedule_next_event_processing(
            db_session=db_session,
            retry=retry
        )

def cancel_next_event_processing() -> None:
    """
    Cancels next scheduled event processing
    """
    global SCHEDULER
    global JOB_ID
    try:
        SCHEDULER.remove_job(JOB_ID)
    except JobLookupError:
        # job is not scheduled
        pass
