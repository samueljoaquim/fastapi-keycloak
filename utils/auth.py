import json
import logging

from contextvars import ContextVar
from datetime import datetime

from fastapi import Depends, HTTPException, status, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyCookie
from jwcrypto.jwt import JWTExpired
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakPostError
from conf import settings, redis_client


logger = logging.getLogger(__name__)

USER_INFO_PREFIX = "userinfo-"

bearer_scheme = HTTPBearer(auto_error=False)
cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_server_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    client_secret_key=settings.keycloak_client_secret,
)

request_context = ContextVar("request_context", default=dict())


def session_data(
    response: Response,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    access_token: str = Depends(cookie_scheme),
):

    try:
        if access_token:
            scheme, token = access_token.split(" ")
            credentials = HTTPAuthorizationCredentials(scheme=scheme, credentials=token)
        elif not credentials:
            raise Exception()

        token = credentials.credentials

        try:
            token_info = keycloak_openid.decode_token(token)
        except JWTExpired:
            session_data = refresh_token(response=response, expired_token=token)
        else:
            if datetime.fromtimestamp(token_info["exp"]) < datetime.now():
                session_data = refresh_token(response=response, expired_token=token)
            else:
                key = f"{USER_INFO_PREFIX}{token_info["jti"]}"

                # Verify if session data is available in Redis
                session_data_str = redis_client.get(key)
                if not session_data_str:
                    raise Exception("No session data")
                session_data = json.loads(session_data_str)

        return session_data

    except KeycloakPostError as ke:
        logger.exception(ke)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, json.loads(ke.response_body))
    except Exception as e:
        logger.exception(e)
        message = (
            e.args[0]
            if e.args and isinstance(e.args[0], str)
            else "User doesn't have access to the resource"
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, message)


def verify_role(role):
    def inner(session_data=Depends(session_data)):
        try:
            verify_role_present(role, session_data)
        except AssertionError as e:
            logger.warning(
                f"User '{session_data['preferred_username']}' doesn't have required role '{role}'"
            )
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "User doesn't have access to the resource"
            )

    return inner


def verify_role_present(role, session_data):
    assert role in session_data["decoded"]["access_token"]["resource_access"].get(
        "fastapi-keycloak", {}
    ).get("roles", {})


def save_session_data(token_info):
    decoded_token = keycloak_openid.decode_token(token_info["access_token"])
    decoded_id_token = keycloak_openid.decode_token(token_info["id_token"])
    session_data = {
        **token_info,
        "decoded": {"access_token": decoded_token, "id_token": decoded_id_token},
    }
    verify_role_present("read-data", session_data)
    key = f"{USER_INFO_PREFIX}{decoded_token["jti"]}"
    redis_client.set(key, json.dumps(session_data))
    return session_data


def refresh_token(expired_token, response: Response):
    # Refresh token and save new data in session
    expired_token_info = keycloak_openid.decode_token(expired_token, validate=False)
    expired_key = f"{USER_INFO_PREFIX}{expired_token_info["jti"]}"
    logger.info("Token expired, refreshing")
    expired_session_data = redis_client.get(expired_key)
    if not expired_session_data:
        raise Exception("Session is expired")
    expired_session_data = json.loads(expired_session_data)
    # Delete old key
    redis_client.delete(expired_key)
    token_info = keycloak_openid.refresh_token(expired_session_data["refresh_token"])
    set_auth_cookie(token_info["access_token"], response)
    return save_session_data(token_info)


def set_auth_cookie(access_token, response: Response):
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
    )
