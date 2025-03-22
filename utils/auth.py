import json
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyCookie
from jwcrypto.jwt import JWTExpired
from keycloak import KeycloakOpenID

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


def session_data(
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

        token_info = keycloak_openid.decode_token(token)
        key = f"{USER_INFO_PREFIX}{token_info["jti"]}"

        # Verify if session data is available in Redis
        session_data = redis_client.get(key)
        if not session_data:
            raise Exception("No session data")

        return json.loads(session_data)
    except JWTExpired as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token is expired")
    except Exception as e:
        logger.exception(e)
        message = e.args[0] if e.args else "User doesn't have access to the resource"
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
    assert role in session_data["decoded"]["access_token"]["resource_access"].get("fastapi-keycloak", {}).get(
        "roles", {}
    )
