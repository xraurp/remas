from string import Template
from src.db.models import (
    Node,
    Resource,
    ResourceAllocation,
    Task,
    User,
    NotificationType,
    Notification
)
import httpx
import json
from src.config import get_settings
from fastapi import HTTPException
from src.app_logic.notification_operations import get_all_notifications_for_user
from src.app_logic.authentication import is_admin
from src.schemas.grafana_entities import GrafanaAlertLabels

def join_url_path(*args) -> str:
    """
    Joins parts of URL path together.
    :param args: parts of the URL paths to join
    :return (str): joined URL path
    """
    return '/'.join(map(lambda x: str(x).strip('/'), args))

def upload_grafana_config(
    config: dict,
    path: str,
    method: str = 'POST'
) -> httpx.Response:
    """
    Uploads configuration to grafana instance.
    :param config (dict): configuration to upload (json)
    :Param path (str): location on the instance where to upload the config
        -> (https://grafana.instance/{path}) <-
    :param method (str): HTTP method (POST, GET, etc.) (default: POST)
    :return (httpx.Response): response
    """
    response = httpx.request(
        method=method,
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password),
        json=config
    )
    # Raise error with response message with error has occured
    response.raise_for_status()
    return response

def remove_grafana_config(path: str) -> None:
    """
    Removes configured entity (like alert rule, dashboard, etc.) from Grafana.
    :param path (str): path to given entity
    """
    response = httpx.request(
        method='DELETE',
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password)
    )
    response.raise_for_status()

def get_grafana_config(path: str) -> httpx.Response:
    """
    Gets config from given API path from Grafana.
    :param path (str): path on Grafana instance API
    :return (httpx.Response): response
    """
    response = httpx.request(
        method='GET',
        url=join_url_path(get_settings().grafana_url, path),
        auth=(get_settings().grafana_username, get_settings().grafana_password),
    )
    # Raise error with response message with error has occured
    response.raise_for_status()
    return response

def grafana_add_node_dashboard(node: Node) -> None:
    """
    Creates dashboard for given node in Grafana.
    :param node (Node): node to add dashboard for
    """
    template = Template(node.dashboard_template.template)
    dashboard_folder = get_folders_from_grafana(
        folder_names=['node_dashboards']
    )[0]

    dashboard_config = template.safe_substitute(
        node_id=node.id,
        node_name=node.name,
        node_description=node.description
    )
    dashboard_config = json.loads(dashboard_config)
    dashboard_config['folderUid'] = dashboard_folder['uid']
    dashboard_config['message'] = 'Created node dashboard on node init.'

    # Upload config to grafana
    try:
        upload_grafana_config(
            config=dashboard_config,
            path='/api/v1/provisioning/alert-rules'
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create dashboard for node in Grafana!"
        )

# TODO - remove node dashboard
# TODO - update node dashboard

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
    config = json.loads(config)

    # Set alert labels
    labels = GrafanaAlertLabels(
        default=True if allocation_amount is None else False,
        username=user.username,
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
                detail=f"Failed to create alert for user {user.username} in "
                        "Grafana!"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update alert for user {user.username} in "
                        "Grafana!"
            )

def get_folders_from_grafana(folder_names: list[str]) -> list[dict]:
    """
    Gets folders with given names from Grafana.
    :param folder_names (list[str]): list of folder names
    :return (list[dict]): folders from Grafana
    """
    try:
        folders = get_grafana_config('/api/folders').json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get folder list from Grafana!"
        )
    
    return list(filter(
        lambda f: f.get('title', '') in folder_names,
        folders
    ))

def get_user_notifications_by_type(
    types: list[NotificationType],
    user: User
) -> list[Notification]:
    """
    Returns all user notification with specified types.
    :param types (list[NotificationType]): types of notification to return
    :param user (User): user whose notifications to return
    :return (list[Notification]): notifications with tyven types
    """
    grouped_notifications = get_all_notifications_for_user(user=user)
    user_notifications = []
    for group in grouped_notifications:
        for notification in group.notifications:
            if notification.type not in types:
                continue
            # remove duplicates
            if notification in user_notifications:
                continue
            
            user_notifications.append(notification)
    return user_notifications

def grafana_add_task_alert(
    task: Task,
    resource_allocation: ResourceAllocation,
    notification: Notification
) -> None:
    """
    Adds Grafana user alert rule for certain resource that will be
    used when task runs to notify user about exceeding the limit.
    This is applied when task starts.
    :param task (Task): task to add alert for
    :param resource_allocation (ResourceAllocation): resource allocation entity
        for given resource on given node
    :param notification (Notification): notifiction with template for alert
    """
    user = task.User
    node = resource_allocation.node
    resource = resource_allocation.resource

    node_provides_resource = None
    for npr in node.resources:
        if npr.resource == resource:
            node_provides_resource = npr
            break
    
    if not node_provides_resource:
        raise HTTPException(
            status_code=500,
            detail="Node does not provide requested resource!"
        )
    
    folder = get_folders_from_grafana(
        folder_names=[f'{user.username}_task_alerts']
    )[0]

    grafana_add_or_update_alert_rule(
        user=user,
        node=node,
        resource=resource,
        notification=notification,
        folder_uid=folder['uid'],
        resource_amount=node_provides_resource.amount,
        allocation_amount=resource_allocation.amount
    )

# TODO - remove task alert
# TODO - update task alert

def grafana_add_all_task_allerts(task: Task) -> None:
    """
    Adds all Grafana alerts for given task to Grafana.
    This sets up user resource usage limits in Grafana for given task.
    :param task (Task): task to add alerts for
    """
    # get list of relevant alerts/notifications to add to Grafana
    user_notifications = get_user_notifications_by_type(
        types=[NotificationType.grafana_resource_exceedance_task],
        user=task.owner
    )
    
    # add notifications for each resource on each node
    for resource_allocation in task.resource_allocations:
        for notification in resource_allocation.resource.notifications:
            if notification not in user_notifications:
                continue

            grafana_add_task_alert(
                task=task,
                resource_allocation=resource_allocation,
                notification=notification
            )

# TODO - add task alert
# TODO - remove task alert
# TODO - update task alert

def grafana_add_default_user_alert(
    user: User,
    notification: Notification,
    existing_user_alerts: list[dict]
) -> None:
    """
    Adds default user alert to Grafana.
    :param user (User): user to add alert for
    :param notification (Notification): notification/alert to add
    :param existing_user_alerts (list[dict]): existing user alerts from Grafana
    """
    folder = get_folders_from_grafana(
        folder_names=[f'{user.username}_task_alerts']
    )[0]

    notification_alerts = list(filter(
        lambda a: a.get('labels', {}).get('notification_id', None) == \
            notification.id,
        existing_user_alerts
    ))

    # add new alerts
    for node_provides_resource in notification.resource.nodes:
        node = node_provides_resource.node

        existing_alert = None
        for alert in notification_alerts:
            if alert.get('labels', {}).get('node_id', None) == node.id and \
               alert.get('labels', {}).get('resource_id', None) == \
               node_provides_resource.resource.id:
                existing_alert = alert
                break

        if not existing_alert:
            grafana_add_or_update_alert_rule(
                user=user,
                node=node,
                resource=notification.resource,
                notification=notification,
                folder_uid=folder['uid'],
                resource_amount=node_provides_resource.amount,
                existing_alert=existing_alert
            )

def grafana_add_all_default_user_alerts(user: User) -> None:
    """
    Adds all Grafana alerts for default resource usage without task.
    :param user (User): user to add alerts for
    """
    # get default alerts / notifications from db
    user_notifications = get_user_notifications_by_type(
        types=[NotificationType.grafana_resource_exceedance_task],
        user=user
    )

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

    # add alerts to Grafana
    for notification in user_notifications:
        # skip if notification has no default amount
        # (is used only when tasks are running)
        if notification.default_amount is None:
            continue

        grafana_add_default_user_alert(
            user=user,
            notification=notification,
            existing_user_alerts=user_alerts
        )

def grafana_add_or_update_user_folders(
    user: User,
    user_grafana_id: str
) -> None:
    """
    Adds all Grafana folders for given user.
    :param user (User): user to add folders for
    :param user_grafana_uid (str): Grafana user ID
    """
    user_system_folders = [
        Template(f).safe_substitute(user_name=user.username)
        for f in get_settings().grafana_user_system_folder_templates
    ]
    user_folders = [
        Template(f).safe_substitute(user_name=user.username)
        for f in get_settings().grafana_user_folder_templates
    ]

    # filter system folders
    existing_system_folders = get_folders_from_grafana(
        folder_names=user_system_folders
    )
    existing_system_folders_names = [
        f['title'] for f in existing_system_folders
    ]

    # filder user folders
    existing_user_folders = get_folders_from_grafana(
        folder_names=user_folders
    )
    existing_user_folders_names = [
        f['title'] for f in existing_user_folders
    ]

    # create missing system folders
    for folder in user_system_folders:
        if folder in existing_system_folders_names:
            continue

        try:
            upload_grafana_config(
                config={'uid': None, 'title': folder},
                path='/api/folders'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create folder for user {user.username} "
                        "in Grafana!"
            )
    
    # create missing user folders
    for folder in user_folders:
        if folder not in existing_user_folders_names:
            try:
                upload_grafana_config(
                    config={'uid': None, 'title': folder},
                    path='/api/folders'
                )
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create folder for user {user.username} "
                            "in Grafana!"
                )
        
        ### change user folder permissions, so user can edit the content
        created_folder = get_folders_from_grafana(
            folder_names=[folder]
        )[0]

        # get folder permissions
        try:
            permissions = get_grafana_config(
                f'/api/folders/{created_folder["uid"]}/permissions'
            ).json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get permissions for folder "
                       f"{created_folder['title']} in Grafana!"
            )
        
        # check if user is already set as editor
        permissions_set = False
        for permission in permissions:
            if permission['userId'] == user_grafana_id \
            and permission['permission'] == 2:
                permissions_set = True
                break
        if permissions_set:
            continue

        # add user to folder as editor
        permissions.append({
            'userId': user_grafana_id,
            'permission': 2  # Editor
        })
        try:
            upload_grafana_config(
                config={'items': permissions},
                path=f'/api/folders/{created_folder["uid"]}/permissions'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add user {user.username} permissions to "
                       f"folder {created_folder['title']} in Grafana!"
            )

def grafana_add_or_update_contact_point(user: User) -> None:
    """
    Adds or updates contact point for user.
    :param user (User): user to add contact point for
    """
    contact_point = {
        'uid': None,
        'name': f'{user.username} contact point',
        'type': 'email',
        'settings': {
            'addresses': user.email,
            'singleEmail': False
        },
        'disableResolveMessage': False
    }

    # get existing contact points
    try:
        existing_contact_points = get_grafana_config(
            '/api/v1/provisioning/contact-points'
        ).json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contact points from Grafana!"
        )
    
    # find existing contact point
    for cp in existing_contact_points:
        if cp['name'] == contact_point['name']:
            contact_point['uid'] = cp['uid']
            break

    # add or update contact point
    if contact_point['uid'] is None:
        path = '/api/v1/provisioning/contact-points'
        method = 'POST'
    else:
        path = f'/api/v1/provisioning/contact-points/{contact_point["uid"]}'
        method = 'PUT'
    try:
        upload_grafana_config(
            config=contact_point,
            path=path,
            method=method
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add or update contact point for user "
                    f"{user.username} in Grafana!"
        )

def grafana_remove_user_contact_point(user: User) -> None:
    """
    Removes contact point for user.
    :param user (User): user to remove contact point for
    """
    contact_point_name = f'{user.username} contact point'
    try:
        existing_contact_points = get_grafana_config(
            '/api/v1/provisioning/contact-points'
        ).json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contact points from Grafana!"
        )

    for cp in existing_contact_points:
        if cp['name'] != contact_point_name:
            continue

        try:
            remove_grafana_config(
                f'/api/v1/provisioning/contact-points/{cp["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove contact point for user "
                        f"{user.username} in Grafana!"
            )

        break

def grafana_create_or_update_user(
    user: User,
    password: str | None = None
) -> None:
    """
    Creates Grafana user or updates existing user.
    :param user (User): user to create Grafana user for
    :param password (str): password for Grafana user
    """
    ### Crate user in grafana
    user_data = {
        'id': None,
        'name': f'{user.name} {user.surname}',
        'login': user.username,
        'email': user.email,
        'isDisabled': False
    }
    if password is not None:
        user_data['password'] = password
    
    grafana_user_id = None
    
    upload_path = '/api/admin/users'
    upload_method = 'POST'

    # get user from grafana
    try:
        grafana_user = get_grafana_config(
            f'/api/users/lookup?loginOrEmail={user.username}'
        ).json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            grafana_user = None
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user {user.username} in Grafana!"
            )
    
    if grafana_user is not None:
        upload_path = f'/api/users/{grafana_user["id"]}'
        upload_method = 'PUT'
        grafana_user_id = grafana_user['id']
    elif password is None:
        raise HTTPException(
            status_code=500,
            detail=f"Error when creating user {user.username} in Grafana! "
                    "Password is not set!"
        )

    # Add user to Grafana 
    try:
        grafana_user = upload_grafana_config(
            config=user_data,
            path=upload_path,
            method=upload_method
        ).json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user {user.username} in Grafana!"
        )
    
    # Get user id when new user is created (on update, id is not returned
    # in the response)
    if upload_method == 'POST':
        grafana_user_id = grafana_user['id']
    
    # Set admin permissions in Grafana
    if is_admin(user=user):
        try:
            upload_grafana_config(
                config={'isGrafanaAdmin': True},
                path=f"/api/admin/users/{grafana_user_id}/permissions",
                method='PUT'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to set user {user.username} as admin in "
                        "Grafana!"
            )
    
    ### Create user contact point
    grafana_add_or_update_contact_point(user=user)

    ### Create user folders
    grafana_add_or_update_user_folders(user=user, user_grafana_id=grafana_user_id)

    ### Create default user alerts
    grafana_add_all_default_user_alerts(user=user)

def grafana_remove_user(user: User) -> None:
    """
    Removes Grafana user for user.
    :param user (User): user to remove Grafana user for
    """
    ### remove user alerts
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

    ### remove user folders
    # get user folders
    user_folder_names = [
        Template(f).safe_substitute(user_name=user.username)
        for f in get_settings().grafana_user_system_folder_templates
    ] + [
        Template(f).safe_substitute(user_name=user.username)
        for f in get_settings().grafana_user_folder_templates
    ]

    folders = get_folders_from_grafana(folder_names=user_folder_names)

    # remove user folders
    for folder in folders:
        try:
            remove_grafana_config(
                path=f'/api/folders/{folder["uid"]}'
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to remove folder for user {user.username} "
                        "in Grafana!"
            )

    ### remove user contact point
    grafana_remove_user_contact_point(user=user)

    ### remove user
    # get user
    try:
        grafana_user = get_grafana_config(
            f'/api/users/lookup?loginOrEmail={user.username}'
        ).json()
    except httpx.HTTPStatusError as e:
        # user not in grafana
        if e.response.status_code == 404:
            return
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get user {user.username} in Grafana!"
            )
    
    # remove user
    try:
        remove_grafana_config(
            path=f'/api/admin/users/{grafana_user["id"]}'
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove user {user.username} in Grafana!"
        )


from src.config import get_settings
from sqlmodel import create_engine, Session
from src.db.models import User
session = Session(bind=create_engine(url=get_settings().database_url))
user = session.get(User, 2)
grafana_create_or_update_user(user=user, password='test')
#grafana_remove_user(user=user)
