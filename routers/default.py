import logging
from fastapi import APIRouter
from fastapi.responses import RedirectResponse


logger = logging.getLogger(__name__)

default_router = APIRouter()


@default_router.get("/", response_class=RedirectResponse, include_in_schema=False)
async def info() -> dict:
    return RedirectResponse(url="/auth/login")
