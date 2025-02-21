from pydantic import BaseModel
from src.db.models import User


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class CurrentUserInfo(BaseModel):
    is_admin: bool
    user_id: int
    username: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class SetUserPasswordRequest(BaseModel):
    user_id: int
    new_password: str
