from fastapi import FastAPI
from routers import auth_router, api_router, default_router


app = FastAPI()
app.include_router(default_router)
app.include_router(auth_router)
app.include_router(api_router)
