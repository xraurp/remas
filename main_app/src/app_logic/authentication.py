from sqlmodel import select, Session
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from src.schemas.authentication_entities import (
    TokenResponse,
    CurrentUserInfo,
    ChangePasswordRequest,
    SetUserPasswordRequest
)
from src.db.models import User, Group
from src.config import get_settings
from datetime import datetime, timedelta, timezone
from typing import Annotated
import bcrypt
import logging
from src.app_logic.grafana_user_operations import (
    grafana_change_user_password
)
from src.app_logic.auxiliary_operations import is_admin
import json


oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")

# Dependency injection for token, used in endpoint requiring authentication
tokenDep = Annotated[str, Depends(oauth2_scheme)]

insufficientPermissionsException = HTTPException(
    status_code=403,
    detail="Insufficient permissions!"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if entered password matches the one in the database.
    :param plain_password (str): plain text password
    :param hashed_password (str): hashed password from database (including salt)
    :return (bool): True if passwords match, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """
    Generates password hash using bcrypt. Hash contains salt.
    :param password (str): password to hash
    :return (str): hashed password
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def authenticate_user(
    username: str,
    password: str,
    db_session: Session
) -> User:
    """
    Authenticates user - checks if entered username and password match the
    ones in the database.
    """
    user = db_session.exec(
        select(User).where(User.username == username)
    ).first()
    error = HTTPException(
        status_code=401,
        detail="Wrong username or password!"
    )
    if not user:
        raise error
    if not verify_password(password, user.password):
        raise error
    return user

def create_token(token_data: dict) -> str:
    """
    Creates new jwt access token.
    :param token_data (dict): data to encode in token
        (subject, admin permissions, etc.)
    :return (str): JWT access token
    """
    settings = get_settings()
    data = token_data.copy()
    if data['is_refresh_token']:
        interval = timedelta(
            minutes=settings.token_refresh_expire_minutes
        )
    else:
        interval = timedelta(
            minutes=settings.token_access_expire_minutes
        )
    data['exp'] = datetime.now(timezone.utc) + interval
    return jwt.encode(
        payload=data,
        key=settings.token_secret_key,
        algorithm=settings.token_signing_algorithm
    )

def login(username: str, password: str, db_session: Session) -> TokenResponse:
    """
    Checks user login credentials and returns new token.
    :param username (str): username
    :param password (str): password
    :param db_session (Session): database session to use
    :return (TokenResponse): JWT token and its type
    """
    user = authenticate_user(
        username=username,
        password=password,
        db_session=db_session
    )
    admin_status = is_admin(user=user)
    access_token = create_token(token_data={
        'user_id': user.id,
        'sub': user.username,
        'is_admin': admin_status,
        'is_refresh_token': False
    })
    refresh_token = create_token(token_data={
        'user_id': user.id,
        'sub': user.username,
        'is_admin': admin_status,
        'is_refresh_token': True
    })
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

def refresh_token(
    current_user: CurrentUserInfo,
    db_session: Session
) -> TokenResponse:
    """
    Refreshes access and refresh tokens
    :param current_user (CurrentUserInfo): user info
    :param db_session (Session): database session
    :return (TokenResponse): JWT token
    """
    user = db_session.get(User, current_user.user_id)
    admin_status = is_admin(user=user)
    token = create_token(token_data={
        'user_id': user.id,
        'sub': user.username,
        'is_admin': admin_status,
        'is_refresh_token': False
    })
    refresh_token = create_token(token_data={
        'user_id': user.id,
        'sub': user.username,
        'is_admin': admin_status,
        'is_refresh_token': True
    })
    return TokenResponse(access_token=token, refresh_token=refresh_token)
    
    

def verify_token_data(token: str) -> dict:
    """
    Verifies token and returns its data.
    :return (dict): token data
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if settings.debug:
        try:
            # decode without verifying signature
            decoded = jwt.decode(
                jwt=token,
                key=settings.token_secret_key,
                algorithms=[settings.token_signing_algorithm],
                verify=False
            )
            logging.debug(f'Token: {json.dumps(decoded, indent=4)}')
        except InvalidTokenError as e:
            logging.debug(f'Failed to decode token for debbuging: {e}')
    
    try:
        token_data = jwt.decode(
            jwt=token,
            key=settings.token_secret_key,
            algorithms=[settings.token_signing_algorithm],
            options={
                'verify_signature': True,
                'require': [
                    'exp',
                    'sub',
                    'user_id',
                    'is_admin',
                    'is_refresh_token'
                ],
                'verify_exp': True
            }
        )
    except InvalidTokenError as e:
        logging.error(f'{e}')
        raise credentials_exception

    return token_data

def verify_login(token: tokenDep) -> CurrentUserInfo:
    """
    Verifies access token and returns current user information
        (user that send the request).
    :return (CurrentUserInfo): Current user info - user_id, username, is_admin
    """
    token_data = verify_token_data(token=token)

    if token_data['is_refresh_token']:
        raise HTTPException(
            status_code=401,
            detail="Refresh token was used instead of access token!"
        )
    
    return CurrentUserInfo(
        user_id=token_data['user_id'],
        username=token_data['sub'],
        is_admin=token_data['is_admin']
    )

def verify_login_on_refresh(token: tokenDep) -> CurrentUserInfo:
    """
    Verifies refresh token and returns current user information
        (user that send the request).
    :return (CurrentUserInfo): Current user info - user_id, username, is_admin
    """
    token_data = verify_token_data(token=token)

    if not token_data['is_refresh_token']:
        raise HTTPException(
            status_code=401,
            detail="Access token was used instead of refresh token!"
        )
    
    return CurrentUserInfo(
        user_id=token_data['user_id'],
        username=token_data['sub'],
        is_admin=token_data['is_admin']
    )

def change_user_password(
    request: ChangePasswordRequest,
    current_user: CurrentUserInfo,
    db_session: Session
) -> None:
    """
    Changes user password.
    :param request (ChangePasswordRequest): request with old and new password
    :param current_user (CurrentUserInfo): currently logged in user info
    :param db_session (Session): database session to use
    """
    if get_settings().debug:
        logging.debug(f'Changing password for user {current_user.username}')
        logging.debug(f'Old password: {request.old_password}')
        logging.debug(f'New password: {request.new_password}')
    user = authenticate_user(
        username=current_user.username,
        password=request.old_password,
        db_session=db_session
    )
    # TODO - add some password strength estimation
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long!"
        )
    grafana_change_user_password(user=user, password=request.new_password)
    user.password = get_password_hash(password=request.new_password)
    db_session.commit()

def set_user_password(
    request: SetUserPasswordRequest,
    db_session: Session
) -> None:
    """
    Sets user password to the one in the request.
    :param request (SetUserPasswordRequest): request with user id and new 
        password
    :param db_session (Session): database session to use
    """
    user = db_session.get(User, request.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User with id {user_id} not found!"
        )
    grafana_change_user_password(user=user, password=request.new_password)
    user.password = get_password_hash(request.new_password)
    db_session.commit()

def ensure_admin_permissions(current_user: CurrentUserInfo) -> None:
    """
    Checks if current user has admin permissions.
    :param current_user (CurrentUserInfo): currently logged in user info
    :raise HTTPException: if user is not admin
    """
    if not current_user.is_admin:
        raise insufficientPermissionsException
