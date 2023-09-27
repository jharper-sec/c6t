import json

from pathlib import Path

import typer

class ContrastUICredentials:
    base_url: str
    username: str
    superadmin: bool
    password: str
    code: str

    def get_username_from_user_input(self) -> None:
        username = typer.prompt("Email")
        # TODO: Validate username/email
        self.username = username

    def get_password_from_user_input(self) -> None:
        password = typer.prompt("Password", hide_input=True)
        # TODO: Validate password
        self.password = password

    def get_code_from_user_input(self) -> None:
        code = typer.prompt("Code")
        # TODO: Validate code
        self.code = code


class ContrastAPICredentials:
    profile: str
    base_url: str
    username: str
    api_key: str
    service_key: str
    organization_uuid: str
    superadmin: bool

    def get_credentials_from_file(self, profile: str) -> None:
        """
        Get credentials from file in JSON format
        """
        credentials_file_path = Path("~/.c6t/credentials.json").expanduser()
        with open(credentials_file_path, "r") as credentials_file:
            credentials = json.load(credentials_file)
        self.profile = profile
        self.base_url = credentials.get(profile).get("url")
        self.username = credentials.get(profile).get("user_name")
        self.api_key = credentials.get(profile).get("api_key")
        self.service_key = credentials.get(profile).get("service_key")
        self.organization_uuid = credentials.get(profile).get("organization_id")
        self.superadmin = credentials.get(profile).get("superadmin")

    def write_credentials_to_file(self) -> None:
        """
        Write credentials to file in JSON format
        """
        credentials = {
            self.profile: {
                "url": self.base_url,
                "user_name": self.username,
                "api_key": self.api_key,
                "service_key": self.service_key,
                "organization_id": self.organization_uuid,
                "superadmin": self.superadmin,
            }
        }
        credentials_file_path = Path("~/.c6t/credentials.json").expanduser()
        credentials_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(credentials_file_path, "w") as credentials_file:
            json.dump(credentials, credentials_file, indent=4)
