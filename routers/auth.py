import logging
from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from fastapi.responses import RedirectResponse
from typing import Annotated

from keycloak import KeycloakAuthenticationError

from services.auth import AuthService
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
        token_info = AuthService.login(login_data.user, login_data.password)
        return token_info
    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User doesn't have access to the application",
        )
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


@auth_router.get("/login", response_class=RedirectResponse, include_in_schema=False)
async def login_redirect():
    """
    Login using Keycloak interface
    """
    try:
        auth_url = AuthService.login_redirect()
        return RedirectResponse(url=auth_url)
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login not authorized",
        )


@auth_router.post("/logout")
async def logout(response: Response, user_info=Depends(user_info)):
    """
    Login using provided user and password
    """
    try:
        AuthService.logout(user_info["token"])
        response.delete_cookie("access_token")
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not execute user logout",
        )


@auth_router.get("/redirect", include_in_schema=False)
async def redirect(
    query: Annotated[AuthParams, Query()], response: Response
) -> RedirectResponse:
    try:
        access_token_info = AuthService.get_access_token(query.code)
        response = RedirectResponse(url="/pages/home.html")
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token_info['access_token']}",
            httponly=True,
        )
        return response

    except AssertionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User doesn't have access to the application",
        )
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login not authorized",
        )
