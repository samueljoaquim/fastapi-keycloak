import json
import logging
import secrets

from utils.auth import keycloak_openid, USER_INFO_PREFIX, verify_role_present
from conf import redis_client


logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def login(user, password):
        token_info = keycloak_openid.token(user, password)
        token = token_info["access_token"]
        decoded_token = keycloak_openid.decode_token(token)
        verify_role_present("read-data", decoded_token)

        key = f"{USER_INFO_PREFIX}{decoded_token["jti"]}"
        redis_client.set(
            key, json.dumps({"refresh_token": token_info["refresh_token"]})
        )

        return {"access_token": token_info["access_token"]}

    @staticmethod
    def logout(access_token):
        decoded_token = keycloak_openid.decode_token(access_token)
        key = f"{USER_INFO_PREFIX}{decoded_token["jti"]}"
        user_data = json.loads(redis_client.get(key))
        if user_data and "refresh_token" in user_data:
            keycloak_openid.logout(user_data["refresh_token"])
            redis_client.delete(key)

        return True

    @staticmethod
    def login_redirect():
        return keycloak_openid.auth_url(
            redirect_uri="http://fastapi.main.local/auth/redirect",
            nonce=secrets.token_urlsafe(),
            scope="email profile",
            state="login",
        )

    @staticmethod
    def get_access_token(code):
        token_info = keycloak_openid.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri="http://fastapi.main.local/auth/redirect",
        )
        decoded_token = keycloak_openid.decode_token(token_info["access_token"])
        verify_role_present("read-data", decoded_token)
        key = f"{USER_INFO_PREFIX}{decoded_token["jti"]}"
        redis_client.set(
            key, json.dumps({"refresh_token": token_info["refresh_token"]})
        )
        return {"access_token": token_info["access_token"]}
