from pydantic import BaseModel


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
    profile_base_url: str
    base_url: str
