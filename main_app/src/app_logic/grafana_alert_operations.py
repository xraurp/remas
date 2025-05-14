from string import Template
from src.db.models import (
    Node,
    Resource,
    ResourceAllocation,
    Task,
    User,
    NotificationType,
    Notification,
    Task,
    TaskStatus,
    Group
)
import httpx
import json
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from src.schemas.grafana_entities import GrafanaAlertLabels
from src.app_logic.grafana_general_operations import (
    upload_grafana_config,
    remove_grafana_config,
    get_grafana_config,
    get_folders_from_grafana
)
from src.app_logic.auxiliary_operations import (
    get_user_notifications_by_type,
    get_members_including_subgroups
)
from src.config import get_settings
import logging

def grafana_add_or_update_alert_rule(
    user: User,
    node: Node,
    resource: Resource,
    notification: Notification,
    folder_uid: str,
    resource_amount: int,
    allocation_amount: int | None = None,
    existing_alert: dict | None = None
) -> None:
    """
    Adds alert rule to Grafana or updates existing one.
    :param user (User): user to add alert for
    :param node (Node): node to add alert for
    :param resource (Resource): resource to add alert for
    :param notification (Notification): notification with template for alert
    :param folder_uid (str): uid of Grafana folder to add alert to
    :param resource_amount (int): amount of resource provided by the node
    :param allocation_amount (int): amount of resource allocated to the task
    :param existing_alert (dict): existing alert from Grafana to update 
        (alert can be passed in for update, so it doesn't have to be searched
        for again)
    """
    if allocation_amount is not None:
        amount = allocation_amount
    else:
        amount = notification.default_amount
        # Skip if default alerts are being configured.
        # This rule is used only when tasks are running.
        if amount is None:
            return
    
    if not existing_alert:
        # get existing user alerts from Grafana
        try:
            alerts = get_grafana_config(
                '/api/v1/provisioning/alert-rules'
            ).json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get alerts for user {user.username} "
                        "from Grafana!"
            )
        # find alert that matches the user, node, resource and notification
        for alert in alerts:
            al = alert.get('labels', {})
            if al.get('username', None) != user.username:
                continue
            if al.get('notification_id', None) != str(notification.id):
                continue
            if al.get('node_id', None) != str(node.id):
                continue
            if al.get('resource_id', None) != str(resource.id):
                continue
            existing_alert = alert
            break

    contact_point_name = f'{user.username} contact point'

    config = Template(notification.notification_template).safe_substitute(
        user_id = user.id,
        user_name = user.name,
        user_surname = user.surname,
        user_username = user.username,
        user_uid = user.uid,
        user_email = user.email,
        node_id = node.id,
        node_name = node.name,
        node_description = node.description,
        resource_id = resource.id,
        resource_name = resource.name,
        resource_description = resource.description,
        resource_amount = resource_amount,
        allocation_amount = amount
    )
    try:
        config = json.loads(config)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create alert {notification.name} "
                   f"for user {user.username} in Grafana! "
                    "Wrong notification template syntax!"
        )

    if notification.owner:
        owner = notification.owner.username
    else:
        owner = 'admin'

    # Set alert labels
    labels = GrafanaAlertLabels(
        default=True if allocation_amount is None else False,
        username=user.username,
        notification_owner=owner,
        node_id=node.id,
        resource_id=resource.id,
        notification_id=notification.id
    )
    config_labels = config.get('labels', {})
    config_labels |= labels.model_dump()
    config['labels'] = config_labels

    # Set user contact point
    if 'notification_settings' not in config:
        config['notification_settings'] = {}
    config['notification_settings']['receiver'] = contact_point_name

    # Set alert folder in Grafana
    config['folderUID'] = folder_uid
    
    # remove id and set uid
    config['id'] = None
    if existing_alert:
        config['uid'] = existing_alert.get('uid', None)
    else:
        config['uid'] = None

    # Upload config to grafana
    if existing_alert:
        method = 'PUT'
        path = f'/api/v1/provisioning/alert-rules/{config["uid"]}'
    else:
        method = 'POST'
        path = '/api/v1/provisioning/alert-rules'
    
    try:
        upload_grafana_config(
            config=config,
            path=path,
            method=method
        )
    except httpx.HTTPStatusError as e:
        if existing_alert:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create alert {notification.name} "
                       f"for user {user.username} in Grafana!"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update alert {notification.name} "
                       f"for user {user.username} in Grafana!"
            )

def get_tasks_at_timepoint(
    user: User,
    timepoint: datetime,
    db_session: Session,
    lock_rows: bool = False
) -> list[Task]:
    """
    Returns current tasks for given user at given time.
    :param user (User): user to get tasks for
    :param timepoint (datetime): time to get tasks at
    :param db_session (Session): database session to use
    :param lock_rows (bool): whether to lock rows (default: False)
    :return (list[Task]): list of current tasks
    """
    if lock_rows:
        tasks = db_session.query(Task).with_for_update().filter(
            Task.status.in_([TaskStatus.running, TaskStatus.scheduled]),
            Task.owner_id == user.id,
            Task.start_time <= timepoint
        ).all()
    else:
        tasks = db_session.query(Task).filter(
            Task.status.in_([TaskStatus.running, TaskStatus.scheduled]),
            Task.owner_id == user.id,
            Task.start_time <= timepoint
        ).all()

    return tasks

def calculate_required_resources_for_tasks(tasks: list[Task]) -> dict:
    """
    Calculates required resources for given tasks.
    :param tasks (list[Task]): list of tasks to calculate required resources for
    :return (dict): required resources
    """
    required_resources = {}

    for task in tasks:
        for ra in task.resource_allocations:
            if ra.resource_id not in required_resources:
                required_resources[ra.resource_id] = {}
            if ra.node_id not in required_resources[ra.resource_id]:
                required_resources[ra.resource_id][ra.node_id] = ra.amount
            else:
                required_resources[ra.resource_id][ra.node_id] += ra.amount

    return required_resources

def get_current_required_resources(user: User, db_session: Session) -> dict:
    """
    Calculates current required resources for user.
    :param user (User): user to calculate required resources for
    :param db_session (Session): database session to use
    :return (dict): current required resources
    """
    timepoint = datetime.now() + timedelta(
        seconds=get_settings().task_scheduler_precision_seconds
    )
    
    # get current tasks for given user
    tasks = get_tasks_at_timepoint(
        user=user,
        timepoint=timepoint,
        db_session=db_session
    )

    return calculate_required_resources_for_tasks(tasks=tasks)

def grafana_get_existing_user_alerts(
    user: User,
    db_session: Session
) -> list[dict]:
    """
    Gets existing user alerts from Grafana.
    :param user (User): user to get alerts for
    :param db_session (Session): database session to use
    :return (list[dict]): existing user alerts from Grafana
    """
    # get existing user alerts from Grafana
    try:
        alerts = get_grafana_config('/api/v1/provisioning/alert-rules').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts for user {user.username} "
                    "from Grafana!"
        )
    user_alerts = list(filter(
        lambda a: a.get('labels', {}).get('username', None) == user.username,
        alerts
    ))
    return user_alerts

def filter_existing_user_alert(
    user_alerts: list[dict],
    node_id: int,
    resource_id: int,
    notification_id: int
) -> dict | None:
    """
    Filters existing user alert with given parameters from Grafana alerts.
    :precondition: Existing alerts are already filtered by username.
    :param user_alerts (list[dict]): existing user alerts from Grafana
    :param node_id (int): node id to filter by
    :param resource_id (int): resource id to filter by
    :param notification_id (int): notification id to filter by
    :return (dict|None): existing alert with given parameters
    """
    for alert in user_alerts:
        al = alert.get('labels', {})
        if al.get('notification_id', None) != str(notification_id):
            continue
        if al.get('node_id', None) != str(node_id):
            continue
        if al.get('resource_id', None) != str(resource_id):
            continue
        return alert
    return None

def grafana_add_or_update_user_alerts(
    user: User,
    db_session: Session,
    timepoint: datetime = None,
    lock_rows: bool = False
) -> list[HTTPException]:
    """
    Adds or updates Grafana alerts for given user. Also removes alerts that are
    not assigned to user. (Userful when user group is changed etc.)
    :param user (User): user to add alerts for
    :param db_session (Session): database session to use
    :param timepoint (datetime): timepoint to get tasks for
        (to update alerts with correct resource amounts)
    :param lock_rows (bool): lock rows in database until update is finished
    :return (list[HTTPException]): list of errors
    """
    if timepoint is None:
        timepoint = datetime.now() + timedelta(
            seconds=get_settings().task_scheduler_precision_seconds
        )
    
    # get alerts / notifications from db
    user_notifications = get_user_notifications_by_type(
        types=[NotificationType.grafana_resource_exceedance_task],
        user=user
    )

    # get curently required resources for user tasks
    current_tasks = get_tasks_at_timepoint(
        user=user,
        timepoint=timepoint,
        db_session=db_session,
        lock_rows=lock_rows
    )
    required_resources = calculate_required_resources_for_tasks(
        tasks=current_tasks
    )

    # get existing user alerts from Grafana
    user_alerts = grafana_get_existing_user_alerts(
        user=user,
        db_session=db_session
    )

    # get user alert folder from Grafana
    taks_alert_folder = get_folders_from_grafana(
        folder_names=[f'{user.username}_task_alerts']
    )[0]
    general_alert_folder = get_folders_from_grafana(
        folder_names=[f'{user.username}_general_alerts']
    )[0]

    errors = []

    # add alerts to Grafana
    for notification in user_notifications:
        resource = notification.resource

        for node_provides_resource in resource.nodes:
            node = node_provides_resource.node

            # filter existing alert
            existing_alert = filter_existing_user_alert(
                user_alerts=user_alerts,
                node_id=node.id,
                resource_id=resource.id,
                notification_id=notification.id
            )

            # add or update alert
            if resource.id in required_resources and \
               node.id in required_resources[resource.id]:
                amount = required_resources[resource.id][node.id]
            else:
                amount = None
            
            folder = taks_alert_folder

            # handle general alerts that do not change with tasks
            if notification.type == \
               NotificationType.grafana_resource_exceedance_general:
                folder = general_alert_folder
                amount = None

            try:
                grafana_add_or_update_alert_rule(
                    user=user,
                    node=node,
                    resource=resource,
                    notification=notification,
                    folder_uid=folder['uid'],
                    resource_amount=node_provides_resource.amount,
                    allocation_amount=amount,
                    existing_alert=existing_alert
                )
            except HTTPException as e:
                if e not in errors:
                    errors.append(e)

            # remove update alert from user's Grafana alert list
            try:
                user_alerts.remove(existing_alert)
            except ValueError:
                # new alert was added to user -> was not in list
                pass

    # remove alerts that are not assigned to user
    for alert in user_alerts:
        try:
            remove_grafana_config(
                path=f'/api/v1/provisioning/alert-rules/{alert["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            er = HTTPException(
                status_code=500,
                detail=f"Failed to remove alert for user {user.username} "
                        "in Grafana!"
            )
            if er not in errors:
                errors.append(er)
    
    for error in errors:
        logging.error(error.detail)
    
    return errors

def grafana_remove_all_user_alerts(user: User) -> None:
    """
    Removes all Grafana alerts for user.
    :param user (User): user to remove alerts for
    """
    # get user alerts
    try:
        alerts = get_grafana_config('/api/v1/provisioning/alert-rules').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts for user {user.username} "
                    "in Grafana!"
        )
    
    # remove user alerts
    for alert in alerts:
        if alert.get('labels', {}).get('username', None) != user.username:
            continue

        try:
            remove_grafana_config(
                path=f'/api/v1/provisioning/alert-rules/{alert["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove alert for user {user.username} "
                        "in Grafana!"
            )

def grafana_add_alert_to_user(
    user: User,
    notification: Notification,
    db_session: Session
) -> list[HTTPException]:
    """
    Adds alert to user in Grafana. Userful when new alert is assigned to user.
    :param user (User): user to add alert for
    :param notification (Notification): notification/alert to add
    :param db_session (Session): database session to use
    :return (list[HTTPException]): list of error messages
    """
    # check if notification is assigned to a resource
    resource = notification.resource
    if not resource:
        return
    
    # get curently required resources for user tasks
    if notification.type == NotificationType.grafana_resource_exceedance_task:
        required_resources = get_current_required_resources(
            user=user,
            db_session=db_session
        )
    else:
        required_resources = {}

    # get existing user alerts from Grafana
    user_alerts = grafana_get_existing_user_alerts(
        user=user,
        db_session=db_session
    )

    # get user alert folder from Grafana
    if notification.type == \
       NotificationType.grafana_resource_exceedance_task:
        folder = get_folders_from_grafana(
            folder_names=[f'{user.username}_task_alerts']
        )[0]
    else:
        folder = get_folders_from_grafana(
            folder_names=[f'{user.username}_general_alerts']
        )[0]
    
    errors = []
    for node_provides_resource in resource.nodes:
        node = node_provides_resource.node

        # filter existing alert
        existing_alert = filter_existing_user_alert(
            user_alerts=user_alerts,
            node_id=node.id,
            resource_id=resource.id,
            notification_id=notification.id
        )

        # add or update alert
        if resource.id in required_resources and \
            node.id in required_resources[resource.id]:
            amount = required_resources[resource.id][node.id]
        else:
            # general alerts receive always None, becase required_resources is
            # set to empty dict
            amount = None
        
        try:
            grafana_add_or_update_alert_rule(
                user=user,
                node=node,
                resource=resource,
                notification=notification,
                folder_uid=folder['uid'],
                resource_amount=node_provides_resource.amount,
                allocation_amount=amount,
                existing_alert=existing_alert
            )
        except HTTPException as e:
            if e not in errors:
                errors.append(e)
        
    for error in errors:
        logging.error(error.detail)
        
    return errors

def grafana_remove_alert_from_user(
    user: User,
    notification: Notification,
    db_session: Session
) -> None:
    """
    Removes alert from user in Grafana. Userful when alert is removed from user.
    :param user (User): user to remove alert for
    :param notification (Notification): notification/alert to remove
    """
    # get existing user alerts from Grafana
    user_alerts = grafana_get_existing_user_alerts(
        user=user,
        db_session=db_session
    )

    for alert in user_alerts:
        if alert.get('labels', {}).get('notification_id', None) != \
           str(notification.id):
            continue

        # remove alert from user
        try:
            remove_grafana_config(
                path=f'/api/v1/provisioning/alert-rules/{alert["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove alert for user {user.username} "
                        "in Grafana!"
            )

def update_grafana_alert_for_all_users_and_groups(
    notification: Notification,
    db_session: Session
) -> list[HTTPException]:
    """
    Updates grafana alert based on notification.
    :param notification (Notification): notification with template to update
    :param db_session (Session): database session to use
    :return (list[HTTPException]): list of error messages
    """
    # get all users affected by notification
    users = notification.receivers_users
    for group in notification.receivers_groups:
        for user in get_members_including_subgroups(group=group):
            if user not in users:
                users.append(user)
    
    errors = []
    for user in users:
        e = grafana_add_alert_to_user(
            notification=notification,
            user=user,
            db_session=db_session
        )
        for error in e:
            if error not in errors:
                errors.append(error)
    
    return errors

def grafana_remove_alert_for_group(
    group: Group,
    notification: Notification,
    db_session: Session
) -> None:
    """
    Removes alert for group.
    :param group (Group): group to remove alert for
    :param notification (Notification): notification/alert to remove
    :param db_session (Session): database session to use
    """
    afected_users = get_members_including_subgroups(group=group)
    
    for user in afected_users:
        grafana_remove_alert_from_user(
            user=user,
            notification=notification,
            db_session=db_session
        )

def grafana_add_alert_to_group(
    group: Group,
    notification: Notification,
    db_session: Session
) -> list[HTTPException]:
    """
    Adds alert to group.
    :param group (Group): group to add alert for
    :param notification (Notification): notification/alert to add
    :param db_session (Session): database session to use
    :return (list[HTTPException]): list of error messages
    """
    afected_users = get_members_including_subgroups(group=group)
    
    errors = []
    for user in afected_users:
        e = grafana_add_alert_to_user(
            user=user,
            notification=notification,
            db_session=db_session
        )
        for error in e:
            if error not in errors:
                errors.append(error)
    
    return errors

def grafana_remove_alert(
    notification: Notification
) -> None:
    """
    Removes alert from Grafana
    :param notification (Notification): notification/alert to remove
    """
    # get existing alert instances
    try:
        alerts = get_grafana_config('/api/v1/provisioning/alert-rules').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts from Grafana!"
        )
    alert_instances = list(filter(
        lambda a: a.get('labels', {}).get('notification_id', None) == \
            str(notification.id),
        alerts
    ))

    # remove alert instances
    for alert in alert_instances:
        try:
            remove_grafana_config(
                path=f'/api/v1/provisioning/alert-rules/{alert["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove alert {notification.name} "
                        "from Grafana!"
            )

def grafana_remove_alert_for_node(
    node: Node,
    notification: Notification
) -> None:
    """
    Removes alert for node.
    :param node (Node): node to remove alert for
    :param notification (Notification): notification/alert to remove
    """
    # get existing alerts
    try:
        alerts = get_grafana_config('/api/v1/provisioning/alert-rules').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alerts from Grafana!"
        )
    alert_instances = list(filter(
        lambda a: a.get('labels', {}).get('notification_id', None) == \
            str(notification.id) and \
            a.get('labels', {}).get('node_id', None) == str(node.id),
        alerts
    ))

    # remove alert instances
    for alert in alert_instances:
        try:
            remove_grafana_config(
                path=f'/api/v1/provisioning/alert-rules/{alert["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove alert {notification.name} "
                        "from Grafana!"
            )

def get_alert_error(errors: list[HTTPException]) -> HTTPException | None:
    """
    Gets error message from list of errors. Selects most severe error code
    for the message.
    :param errors (list[HTTPException]): list of errors
    :return (HTTPException | None): error to raise or None
    """
    if errors:
        msg = '\n'.join([error.detail for error in errors])
        code = max([error.status_code for error in errors])
        return HTTPException(status_code=code, detail=msg)

    return None
