import logging
from fastapi import APIRouter, Request, Response, Depends, status
from conf import settings

from utils.session import verify_role, session_data
from services.keycloak import KeycloakService
from models import UserInfo, UserInput


logger = logging.getLogger(__name__)


api_router = APIRouter(
    prefix="/api",
    tags=["api"],
    dependencies=[Depends(verify_role(settings.app_read_role))],
)


@api_router.get("/user_information")
async def user_information(
    request: Request, session_data=Depends(session_data)
) -> UserInfo:
    """
    Get user information
    """
    decoded_token = session_data["decoded"]["access_token"]
    base_url = (
        request.base_url.replace(scheme="https")
        if settings.app_force_https
        else request.base_url
    )
    user_information = UserInfo(
        roles=decoded_token["resource_access"]["fastapi-keycloak"]["roles"],
        username=decoded_token["sub"],
        email=decoded_token["email"],
        first_name=decoded_token["given_name"],
        last_name=decoded_token["family_name"],
        profile_base_url=f"{settings.keycloak_server_url}realms/{settings.keycloak_realm}/account?referrer={settings.keycloak_client_id}",
        base_url=base_url.__str__(),
    )

    return user_information


@api_router.post(
    "/add_user_to_group", dependencies=[Depends(verify_role(settings.app_write_role))]
)
async def add_user_to_group(user: UserInput):
    token = KeycloakService.get_admin_token()
    user_id = KeycloakService.get_user_id(user.username, token=token)
    if not KeycloakService.check_user_belongs_to_default_group(user_id, token=token):
        KeycloakService.add_user_to_default_group(user_id, token=token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
