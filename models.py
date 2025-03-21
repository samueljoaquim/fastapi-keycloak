from pydantic import BaseModel
from datetime import datetime


class AuthParams(BaseModel):
    state: str
    session_state: str
    iss: str
    code: str


class LoginData(BaseModel):
    user: str
    password: str


class UserInfo(BaseModel):
    roles: list
    username: str
    email: str
    first_name: str
    last_name: str
