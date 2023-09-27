import requests
import base64
from pathlib import Path

from c6t.configure.credentials import ContrastAPICredentials


class AgentConfig:
    def __init__(self, profile: str):
        self.session = requests.Session()
        self.credentials = ContrastAPICredentials()
        self.credentials.get_credentials_from_file(profile=profile)

        self.session.headers.update(
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

    def get_agent_credentials(self, language: str) -> str:
        """
        Get the Agent YAML config from the TeamServer
        """
        url = (
            f"{self.credentials.base_url}/api/ng/"
            f"{self.credentials.organization_uuid}/agents/external/default/"
            f"{language}"
        )
        response = self.session.post(url)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()
        return ""

    def write_agent_config_to_file(self, yaml_text: str, path: str) -> None:
        """
        Write the Agent Config to the file system
        """
        config_path = Path(path)
        with open(config_path, "w") as f:
            f.write(yaml_text)
