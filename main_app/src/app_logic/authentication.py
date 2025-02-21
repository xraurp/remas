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


oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(tokenUrl="token")

# Dependency injection for token, used in endpoint requiring authentication
tokenDep = Annotated[str, Depends(oauth2_scheme)]

#def init_auth() -> None:
#    global oauth2_scheme
#    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

def is_admin(user: User) -> bool:
    """
    Checks if user is admin.
    User is admin when member of group with id == 2 or group that inherites
    from group with id == 2.
    :param user (User): User database entity queried from active database
                        session.
    :return (bool): True if user is admin, False otherwise
    """
    group = user.group
    while group:
        if group.id == 2:
            return True
        group = group.parent

    return False

def create_token(token_data: dict) -> str:
    """
    Creates new jwt access token.
    :param token_data (dict): data to encode in token
        (subject, admin permissions, etc.)
    :return (str): JWT access token
    """
    settings = get_settings()
    data = token_data.copy()
    expiration_time = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    data['exp'] = expiration_time
    return jwt.encode(
        payload=data,
        key=settings.access_token_secret_key,
        algorithm=settings.access_token_signing_algorithm
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
    token = create_token(token_data={
        'user_id': user.id,
        'sub': user.username,
        'is_admin': admin_status
    })
    return TokenResponse(access_token=token, token_type="bearer")

def verify_login(token: tokenDep) -> CurrentUserInfo:
    """
    Verifies token and returns current user information
        (user that send the request).
    :return (CurrentUserInfo): Current user info - user_id, username, is_admin
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = jwt.decode(
            jwt=token,
            key=settings.access_token_secret_key,
            algorithms=[settings.access_token_signing_algorithm],
            options={
                'verify_signature': True,
                'require': ['exp', 'sub', 'user_id', 'is_admin'],
                'verify_exp': True
            }
        )
    except InvalidTokenError as e:
        logging.error(f'{e}')
        raise credentials_exception

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
    user.password = get_password_hash(request.new_password)
    db_session.commit()
