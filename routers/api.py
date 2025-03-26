import logging
from fastapi import APIRouter, Request, Depends
from conf import settings

from utils.session import verify_role, session_data
from models import UserInfo


logger = logging.getLogger(__name__)


api_router = APIRouter(
    prefix="/api", tags=["api"], dependencies=[Depends(verify_role("read-data"))]
)


@api_router.get("/user_information")
async def user_information(request: Request, session_data=Depends(session_data)) -> UserInfo:
    """
    Get user information
    """
    decoded_token = session_data["decoded"]["access_token"]
    base_url = request.base_url.replace(scheme="https") if settings.app_force_https else request.base_url
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


@api_router.post("/write_data", dependencies=[Depends(verify_role("write-data"))])
async def protected2_endpoint(info: dict, session_data=Depends(session_data)) -> dict:
    """
    Write role example
    """
    session_data["request_context"]["info"] = info

    return {"message": "Data was written"}
