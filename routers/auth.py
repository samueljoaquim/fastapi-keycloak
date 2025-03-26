import logging
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status, Response
from fastapi.responses import RedirectResponse
from typing import Annotated
from jwcrypto.jwt import JWTExpired
from conf import settings

from keycloak import KeycloakAuthenticationError

from services.auth import AuthService
from models import LoginData, AuthParams
from utils.session import session_data, remove_session, set_auth_cookie


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
async def login_redirect(request: Request):
    """
    Login using Keycloak interface
    """
    try:
        base_url = request.base_url.replace(scheme="https") if settings.app_force_https else request.base_url
        auth_url = AuthService.login_redirect(base_url)
        return RedirectResponse(url=auth_url)
    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login not authorized",
        )


@auth_router.post("/logout")
async def logout(response: Response, session_data=Depends(session_data)):
    """
    Login using provided user and password
    """
    try:
        AuthService.logout(session_data)
        remove_session(session_data, response)
        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    except KeycloakAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not execute user logout",
        )


@auth_router.get("/redirect", include_in_schema=False)
async def redirect(
    request: Request,
    query: Annotated[AuthParams, Query()],
    response: Response,
) -> RedirectResponse:
    try:
        base_url = request.base_url.replace(scheme="https") if settings.app_force_https else request.base_url
        token_info = AuthService.get_access_token(base_url, query.code)
        response = RedirectResponse(url=f"{base_url}pages/home.html")
        set_auth_cookie(token_info["access_token"], response)
        return response

    except JWTExpired as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User doesn't have access to the application",
        )
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
