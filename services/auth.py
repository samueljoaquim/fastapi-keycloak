import logging
import secrets

from utils.session import keycloak_openid, save_session_data


logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def login(user, password):
        token_info = keycloak_openid.token(user, password)
        session_data = save_session_data(token_info)
        return {"access_token": session_data["access_token"]}

    @staticmethod
    def logout(session_data):
        if "refresh_token" in session_data:
            keycloak_openid.logout(session_data["refresh_token"])

        return True

    @staticmethod
    def login_redirect():
        return keycloak_openid.auth_url(
            redirect_uri="http://fastapi.main.local/auth/redirect",
            nonce=secrets.token_urlsafe(),
            scope="email profile openid",
            state="login",
        )

    @staticmethod
    def get_access_token(code):
        token_info = keycloak_openid.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri="http://fastapi.main.local/auth/redirect",
        )
        session_data = save_session_data(token_info)
        return {"access_token": session_data["access_token"]}
