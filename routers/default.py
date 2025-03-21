import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

default_router = APIRouter()

@default_router.get("/")
async def info() -> dict:
    return {
        "message": "Login through browser using /login (GET method) or through API using /login (POST method)"
    }
