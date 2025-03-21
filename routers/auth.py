import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import RedirectResponse
from typing import Annotated

from keycloak import KeycloakAuthenticationError

from services import LoginService
from models import LoginData, AuthParams
from utils.auth import user_info


logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/login")
async def login(login_data: LoginData) -> dict:
    """
    Login using provided user and password
    """
    try:
        return LoginService.login(login_data.user, login_data.password)
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

@auth_router.get("/login", response_class=RedirectResponse)
async def login_redirect():
    """
    Login using Keycloak interface
    """
    try:
        auth_url = LoginService.login_redirect()
        return RedirectResponse(url=auth_url)
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login not authorized",
        )

@auth_router.post("/logout")
async def logout(user_info = Depends(user_info)) -> dict:
    """
    Login using provided user and password
    """
    try:
        return LoginService.logout(user_info["token"])
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not execute user logout",
        )

@auth_router.get("/redirect", include_in_schema=False)
async def redirect(query: Annotated[AuthParams, Query()]):
    try:
        access_token_info = LoginService.get_authorization_code(query.code)
        return access_token_info["access_token"]
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login not authorized",
        )
