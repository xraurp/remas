from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.app_logic.authentication import (
    login,
    change_user_password,
    set_user_password
)
from src.schemas.authentication_entities import (
    TokenResponse,
    ChangePasswordRequest,
    SetUserPasswordRequest
)
from . import SessionDep, loginDep
from typing import Annotated

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

@authentication_route.post("/change-password", response_model=dict)
def change_password(
    request: ChangePasswordRequest,
    current_user: loginDep,
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
    return {"message": "Password changed successfully!"}

@authentication_route.post("/set-password", response_model=dict)
def set_password(
    request: SetUserPasswordRequest,
    current_user: loginDep,
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
    return {"message": "Password set successfully!"}
