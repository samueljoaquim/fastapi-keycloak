import logging
import requests

from conf import settings


logger = logging.getLogger(__name__)


class KeycloakAPIClient:

    def __init__(self):
        self.base_url = settings.keycloak_server_url
        self.realm = settings.keycloak_admin_realm
        self.client_id = settings.keycloak_admin_client_id
        self.client_secret = settings.keycloak_admin_client_secret
        self.default_group_name = settings.app_default_group
        self.default_group_id = None

    def login(self) -> str:
        response = requests.post(
            f"{self.base_url}realms/{self.realm}/protocol/openid-connect/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
        )
        return response.json()["access_token"]

    def get_user_id(self, token, realm, username) -> str:
        response = requests.get(
            f"{self.base_url}admin/realms/{realm}/users?username={username}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()[0]["id"]

    def get_user_groups(self, token, realm, user_id) -> str:
        response = requests.get(
            f"{self.base_url}admin/realms/{realm}/users/{user_id}/groups/",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()

    def get_default_group_id(self, token, realm) -> str:
        if not self.default_group_id:
            response = requests.get(
                f"{self.base_url}admin/realms/{realm}/groups?search={self.default_group_name}",
                headers={"Authorization": f"Bearer {token}"},
            )
            self.default_group_id = response.json()[0]["id"]

        return self.default_group_id

    def add_user_to_group(self, token, realm, user_id, group_id):
        requests.put(
            f"{self.base_url}admin/realms/{realm}/users/{user_id}/groups/{group_id}",
            headers={"Authorization": f"Bearer {token}"},
        )


api_client = KeycloakAPIClient()


class KeycloakService:

    @staticmethod
    def get_admin_token():
        return api_client.login()

    @staticmethod
    def get_user_id(username, token=None):
        realm = settings.keycloak_realm
        if not token:
            token = api_client.login()
        return api_client.get_user_id(token, realm, username)

    @staticmethod
    def check_user_belongs_to_default_group(user_id, token=None):
        realm = settings.keycloak_realm
        if not token:
            token = api_client.login()
        group_id = api_client.get_default_group_id(token, realm)
        groups = api_client.get_user_groups(token, realm, user_id)
        return group_id in [group["id"] for group in groups]

    @staticmethod
    def add_user_to_default_group(user_id, token=None):
        realm = settings.keycloak_realm
        if not token:
            token = api_client.login()
        group_id = api_client.get_default_group_id(token, realm)
        api_client.add_user_to_group(token, realm, user_id, group_id)
