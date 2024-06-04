import sys

import httpx

import typing
from typing import Any, List, Dict, Optional

import typer

import questionary

from c6t.configure.credentials import ContrastAPICredentials, ContrastUICredentials


class ContrastUIAuthManager:
    def __init__(self, base_url: str):
        self.ui_credentials = ContrastUICredentials()
        self.api_credentials = ContrastAPICredentials()

        self.base_url = base_url
        self.superadmin = False
        self.sso_enabled = False
        self.license_active = False
        self.two_step_verification_enabled = False
        self.client = httpx.Client()

    def login(self, profile: str) -> None:
        """
        This is the main login function. It calls all the other functions
        """
        self.get_session_cookie()
        self.ui_credentials.get_username_from_user_input()
        self.check_sso(self.ui_credentials.username)
        if self.sso_enabled:
            sys.exit("SSO is enabled. Exiting.")
        self.check_if_license_is_active()
        if not self.license_active:
            sys.exit("TeamServer license is not active. Exiting.")
        self.ui_credentials.get_password_from_user_input()
        self.authenticate(self.ui_credentials.username, self.ui_credentials.password)
        self.set_xsrf_token_header()
        if self.two_step_verification_enabled:
            self.ui_credentials.get_code_from_user_input()
            self.authorize(self.ui_credentials.code)

        self.get_profile_roles()
        if self.ui_credentials.superadmin:
            while True:
                toggle_superadmin = typer.prompt("Toggle Superadmin? (y/n)")
                if toggle_superadmin == "y":
                    self.toggle_superadmin()
                    self.get_superadmin_users_roles()
                    self.organization_uuid = self.get_superadmin_organizations()
                    # TODO: SuperAdmin workflow
                    print("SuperAdmin workflow not implemented yet.")
                    break
                elif toggle_superadmin == "n":
                    print("Not using Superadmin.")
                    break
                else:
                    print("Invalid input.")

        organizations = self.get_organizations()
        self.organization_uuid = self.select_organization(organizations)

        self.api_credentials.profile = profile
        self.api_credentials.base_url = self.base_url
        self.api_credentials.username = self.ui_credentials.username
        self.api_credentials.api_key = self.get_api_key(self.organization_uuid)
        self.api_credentials.service_key = self.get_service_key()
        self.api_credentials.organization_uuid = self.organization_uuid
        self.api_credentials.superadmin = self.superadmin

        self.api_credentials.write_credentials_to_file()

    def get_session_cookie(self) -> None:
        """
        This is a hack to get the SESSION cookie set. It isn't
        completely clear why this is necessary. The cookie is set by the
        server in the response to the request. allow_redirects is set to
        False to prevent receiving the forwarded request. If this is not
        done, a 401 error is received and the SESSION cookie is not set.
        """
        try:
            url = f"{self.base_url}/api/ng/agent/feature"
            response = self.client.get(url, follow_redirects=False)
            if response.status_code != 302:
                # If the response is not a 302, the SESSION cookie is not set.
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_information(self) -> None:
        """
        This gets the public information about the server.
        """
        try:
            url = f"{self.base_url}/api/public/ng/information"
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(data.get("messages")[0])
                else:
                    print(data.get("messages")[0])
                    sys.exit(1)
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def check_sso(self, email: str) -> bool:
        """
        This checks if the email address is associated with an SSO account.
        If the response is 200, the email address is associated with an SSO account.
        If the response is 404, the email address is not associated with an SSO account.
        If the response is anything else, raises an exception.
        """
        try:
            url = f"{self.base_url}/api/public/ng/saml/email/{email}"
            response = self.client.get(url)
            if response.status_code == httpx.codes.OK:
                self.sso_enabled = True
            elif response.status_code == httpx.codes.NOT_FOUND:
                self.sso_enabled = False
                data = response.json()
                if data.get("success"):
                    print(data.get("messages")[0])
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)
        return False

    def check_if_license_is_active(self) -> None:
        """
        This checks if the TeamServer license is active.
        If the response is 200, the license is active.
        If the response is anything else, raises an exception.
        """
        try:
            url = f"{self.base_url}/api/ng/contrast/license/active"
            response = self.client.head(url)
            if response.status_code == 200:
                self.license_active = True
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def authenticate(self, username: str, password: str) -> None:
        try:
            url = f"{self.base_url}/authenticate.html"
            data = {
                "ui": False,
                "username": username,
                "password": password,
                "sso": False,
            }
            response = self.client.post(url, data=data)
            if response.status_code == 200:
                data = response.json()
                messages: List[str] = []
                if data.get("success"):
                    messages = typing.cast(List[str], data.get("messages"))
                    print(messages[0])
                    if data.get("toggle_enabled"):
                        # Two-Step Verification (TSV) is enabled
                        self.two_step_verification_enabled = True
                    else:
                        # Two-Step Verification (TSV) is not enabled
                        self.two_step_verification_enabled = False
                else:
                    messages = typing.cast(List[str], data.get("messages"))
                    print(messages[0])
                    sys.exit(1)
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def set_xsrf_token_header(self) -> None:
        """
        This sets the X-XSRF-TOKEN header to the value of the XSRF-TOKEN cookie.
        """
        for cookie in self.client.cookies.jar:
            if cookie.name == "XSRF-TOKEN" and cookie.value:
                self.client.headers.update(
                    {
                        "X-XSRF-TOKEN": cookie.value,
                    }
                )

    def authorize(self, code: str) -> None:
        """
        This authorizes the user with the Two-Step Verification (TSV) code.
        """
        try:
            url = f"{self.base_url}/api/ng/tsv/authorize"
            data = {
                "code": code,
            }
            response = self.client.post(url, json=data)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    messages: List[str] = typing.cast(List[str], data.get("messages"))
                    print(messages[0])
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_profile_roles(self) -> None:
        """
        This gets the roles for the user.
        """
        try:
            url = f"{self.base_url}/api/ng/profile/roles"
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(data.get("messages")[0])
                    if data.get("adminRole") == "SUPERADMIN":
                        self.ui_credentials.superadmin = True
                    else:
                        self.ui_credentials.superadmin = False
                else:
                    print(data.get("messages")[0])
                    sys.exit(1)
            else:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_api_key(self, organization_id: str) -> str:
        """
        This gets the API key for the user.
        """
        try:
            url = f"{self.base_url}/api/ng/{organization_id}/users/keys/apikey"
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return typing.cast(str, data.get("api_key"))
            else:
                response.raise_for_status()
            return ""
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_service_key(self) -> str:
        """
        This gets the Service key for the user.
        """
        try:
            url = f"{self.base_url}/api/ng/profile/servicekey"
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return typing.cast(str, data.get("service_key"))
            else:
                response.raise_for_status()
            return ""
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_organizations(self) -> List[str]:
        """
        Get the organizations from TeamServer
        """
        url = f"{self.base_url}/api/ng/profile/organizations"

        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("count") > 0:
                    return typing.cast(List[str], data.get("organizations"))
                else:
                    print("No organizations found")
                    sys.exit(1)
            else:
                response.raise_for_status()
            return [""]
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def select_organization(self, organizations: Any) -> Any:
        """
        Ask the user to select an organization by index number
        """

        organization_choices: List[Dict[str, Optional[str]]] = []

        for organization in organizations:
            organization_choices.append(
                {
                    "name": organization.get("name"),
                    "value": organization.get("organization_uuid"),
                }
            )

        if len(organization_choices) == 1:
            return organization_choices[0].get("value")

        organization_uuid = questionary.select(
            message="Select your organization:",
            choices=organization_choices,
        ).ask()

        return organization_uuid

    def toggle_superadmin(self) -> None:
        """
        Toggle the SuperAdmin role for the user.
        This is a hack to get the Contrast UI key cookies set.
        Cookies are set as a side-effect of this request.
        """
        url = f"{self.base_url}/api/ng/profile/toggle"
        try:
            response = self.client.get(url)
            if response.status_code != 200:
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_superadmin_users_roles(self) -> List[str]:
        # TODO: This may not be needed.
        # TODO: Determine the meaning of the returned roles.
        """
        Get the SuperAdmin roles for the user
        """
        url = f"{self.base_url}/api/ng/superadmin/users/roles"
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                roles = data.get("roles")
                print(roles)
                return typing.cast(List[str], roles)
            else:
                response.raise_for_status()
            return [""]
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_superadmin_organizations(self) -> str:
        """
        Get the SuperAdmin organizations for the user
        """
        url = (
            f"{self.base_url}/api/ng/superadmin/users/"
            f"{self.ui_credentials.username}/organizations"
        )
        params = {
            "includeDefaultOrgs": True,
        }
        try:
            response = self.client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(data.get("messages")[0])
                    for organization in data.get("organizations"):
                        if organization.get("is_superadmin"):
                            organization_uuid = typing.cast(
                                str, organization.get("organization_uuid")
                            )
                            return organization_uuid
                else:
                    print(data.get("messages")[0])
                    sys.exit(1)
            else:
                response.raise_for_status()
            return ""
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)

    def get_superadmin_api_key(self) -> str:
        """
        Get the SuperAdmin API key for the user
        """
        url = (
            f"{self.base_url}/api/ng/superadmin/users/"
            f"{self.organization_uuid}/keys/apikey"
        )
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                api_key = typing.cast(str, data.get("api_key"))
                return api_key
            else:
                response.raise_for_status()
            return ""
        except httpx.HTTPStatusError as e:
            print(e)
            sys.exit(1)
