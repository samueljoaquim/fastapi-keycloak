import logging
from fastapi import APIRouter
from fastapi.responses import RedirectResponse


logger = logging.getLogger(__name__)

default_router = APIRouter()


@default_router.get("/", response_class=RedirectResponse)
async def info() -> dict:
    return RedirectResponse(url="/auth/login")
