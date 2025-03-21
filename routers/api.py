import logging
from fastapi import APIRouter, Depends

from utils.auth import verify_role, user_info
from models import UserInfo


logger = logging.getLogger(__name__)


api_router = APIRouter(prefix="/api", tags=["api"], dependencies=[Depends(verify_role("read-data"))])

@api_router.get("/user_information")
async def user_information(user_info = Depends(user_info)) -> UserInfo:
    """
    Get user information
    """
    user_information = UserInfo(
        expiration=user_info["exp"],
        token=user_info["token"],
        roles=user_info["resource_access"]["fastapi-keycloak"]["roles"],
        username=user_info["preferred_username"],
        email=user_info["email"],
    )

    return user_information

@api_router.post("/write_data", dependencies=[Depends(verify_role("write-data"))])
async def protected2_endpoint() -> dict:
    """
    Write role example
    """
    return {"message": "Data was written"}
