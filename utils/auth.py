import logging

from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from keycloak import KeycloakOpenID
from typing import Annotated

from conf import settings, redis_client


logger = logging.getLogger(__name__)

USER_INFO_PREFIX = "userinfo-"

bearer_scheme = HTTPBearer(auto_error=False)

keycloak_openid = KeycloakOpenID(
    server_url=settings.keycloak_server_url,
    client_id=settings.keycloak_client_id,
    realm_name=settings.keycloak_realm,
    client_secret_key=settings.keycloak_client_secret,
)


def user_info(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    access_token: Annotated[str | None, Cookie()] = None,
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
        if not redis_client.get(key):
            raise Exception()
        return {**token_info, "token": token}
    except Exception as e:
        logger.exception(e)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "User doesn't have access to the resource"
        )


def verify_role(role):
    def inner(user_info=Depends(user_info)):
        try:
            verify_role_present(role, user_info)
        except AssertionError as e:
            logger.warning(
                f"User '{user_info['preferred_username']}' doesn't have required role '{role}'"
            )
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "User doesn't have access to the resource"
            )

    return inner


def verify_role_present(role, decoded_token):
    assert role in decoded_token["resource_access"].get("fastapi-keycloak", {}).get(
        "roles", {}
    )
