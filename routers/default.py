import logging
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from conf import settings


logger = logging.getLogger(__name__)

default_router = APIRouter()


@default_router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def info(request: Request) -> dict:
    base_url = request.base_url.replace(scheme="https") if settings.app_force_https else request.base_url
    return RedirectResponse(url=f"{base_url}auth/login")
