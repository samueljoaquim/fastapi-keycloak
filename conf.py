from typing import Optional
from redis import Redis
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    app_force_https: bool
    app_default_group: Optional[str] = "fastapi-keycloak-read"
    app_read_role: Optional[str] = "read-data"
    app_write_role: Optional[str] = "write-data"

    keycloak_server_url: str

    keycloak_realm: str
    keycloak_client_id: str
    keycloak_client_secret: str

    keycloak_admin_realm: str
    keycloak_admin_client_id: str
    keycloak_admin_client_secret: str

    redis_host: str
    redis_port: int

    model_config = SettingsConfigDict()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
redis_client = Redis(host=settings.redis_host, port=settings.redis_port)
