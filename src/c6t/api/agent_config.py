import httpx
import base64
from pathlib import Path
import yaml

from c6t.configure.credentials import ContrastAPICredentials


class AgentConfig:
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

    def get_agent_credentials(self, language: str) -> str:
        """
        Get the Agent YAML config from the TeamServer
        """
        url = (
            f"{self.credentials.base_url}/api/ng/"
            f"{self.credentials.organization_uuid}/agents/external/default/"
            f"{language}"
        )
        response = self.client.post(url)
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()
        return ""

    def write_agent_config_to_file(self, text: str, path: str) -> None:
        """
        Write the Agent Config to the file system
        """
        config_path = Path(path)
        with open(config_path, "w") as f:
            f.write(text)

    def validate_agent_config_file_is_valid_yaml(self, path: str) -> bool:
        """
        Validate the Agent Config file is valid YAML
        """
        config_path = Path(path)
        with open(config_path, "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError:
                return False
        return True
