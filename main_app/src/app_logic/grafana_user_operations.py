from src.db.models import (
    User
)
from fastapi import HTTPException
from string import Template
from sqlalchemy.orm import Session
import httpx
from src.app_logic.authentication import is_admin
from src.config import get_settings
from src.app_logic.grafana_general_operations import (
    upload_grafana_config,
    remove_grafana_config,
    get_grafana_config,
    get_folders_from_grafana
)
from src.app_logic.grafana_alert_operations import (
    grafana_add_or_update_user_alerts,
    grafana_remove_all_user_alerts
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
    db_session: Session,
    password: str | None = None
) -> None:
    """
    Creates Grafana user or updates existing user.
    :param user (User): user to create Grafana user for
    :param db_session (Session): database session to use
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
    grafana_add_or_update_user_alerts(user=user, db_session=db_session)

def grafana_remove_user(user: User) -> None:
    """
    Removes Grafana user for user.
    :param user (User): user to remove Grafana user for
    """
    ### remove user alerts
    grafana_remove_all_user_alerts(user=user)

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

# TODO - remove
from src.config import get_settings
from sqlmodel import create_engine, Session
from src.db.models import User
session = Session(bind=create_engine(url=get_settings().database_url))
user = session.get(User, 2)
#grafana_create_or_update_user(user=user, password='test', db_session=session)
grafana_remove_user(user=user)
