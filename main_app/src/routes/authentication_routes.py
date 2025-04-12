from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.app_logic.authentication import (
    login,
    change_user_password,
    set_user_password,
    verify_login_on_refresh,
    refresh_token
)
from src.schemas.authentication_entities import (
    TokenResponse,
    ChangePasswordRequest,
    SetUserPasswordRequest,
    CurrentUserInfo
)
from . import SessionDep, LoginDep
from typing import Annotated

RefreshDep = Annotated[CurrentUserInfo, Depends(verify_login_on_refresh)]

authentication_route = APIRouter(
    prefix="/authentication"
)

@authentication_route.post("/token", response_model=TokenResponse)
def get_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
) -> TokenResponse:
    """
    Returns JWT token to use for authentication in future requests.
    """
    return login(
        username=form_data.username,
        password=form_data.password,
        db_session=session
    )

@authentication_route.post("/refresh", response_model=TokenResponse)
def get_new_token(
    current_user: RefreshDep,
    session: SessionDep
) -> TokenResponse:
    """
    Returns new JWT token to use for authentication in future requests.
    Used to refresh token befere it expires, so the user is not logged out.
    """
    return refresh_token(current_user=current_user, db_session=session)

@authentication_route.post("/change_password", response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: LoginDep,
    session: SessionDep
) -> dict:
    """
    Changes user password.
    """
    change_user_password(
        request=request,
        current_user=current_user,
        db_session=session
    )
    return {'detail': 'Password changed successfully!'}

@authentication_route.post("/set_password", response_model=dict)
def set_password(
    request: SetUserPasswordRequest,
    current_user: LoginDep,
    session: SessionDep
) -> dict:
    """
    Sets user password to the one in the request.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions!"
        )
    set_user_password(
        request=request,
        db_session=session
    )
    return {'detail': 'Password set successfully!'}
