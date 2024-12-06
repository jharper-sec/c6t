import httpx
import base64

from c6t.configure.credentials import ContrastAPICredentials


class Applications:
    def __init__(self, profile: str):
        self.client = httpx.Client()
        self.credentials = ContrastAPICredentials()
        self.credentials.get_credentials_from_file(profile=profile)

        self.client.headers.update(
            {
                "API-Key": self.credentials.api_key,
                "Authorization": self._create_authorization_header(),
            }
        )

    def _create_authorization_header(self) -> str:
        """
        Create the Authorization header for the TeamServer API
        """
        unencoded_authorization_header = (
            f"{self.credentials.username}:{self.credentials.service_key}"
        )
        encoded_authorization_header = base64.b64encode(
            unencoded_authorization_header.encode("utf-8")
        )
        return encoded_authorization_header.decode("utf-8")

    def get_app_id_from_name(self, app_name: str) -> str:
        """
        Get the App ID from the App Name
        """
        url = f"{self.credentials.base_url}/api/ng/{self.credentials.organization_uuid}/applications/filter"
        params = {"offset": 0, "limit": 1}
        payload = {
            "filterText": app_name,
        }
        response = self.client.post(url, params=params, json=payload)
        if response.status_code == 200:
            return response.json().get("applications")[0].get("app_id")
        else:
            response.raise_for_status()
        return ""

    def reset_application(self, app_id: str) -> str:
        """
        Reset the Application
        """
        url = f"{self.credentials.base_url}/api/ng/{self.credentials.organization_uuid}/applications/{app_id}/reset"
        params = {"async": "true"}
        response = self.client.put(url, params=params)
        if response.status_code == 200:
            return response.json().get("messages")[0]
        else:
            response.raise_for_status()
        return ""
