import json
import re
import base64

import typing
from typing import Any, Dict, List

import httpx

from c6t.configure.credentials import ContrastAPICredentials


def load_config() -> Dict[str, Any]:
    with open("config.json", "r") as config_data:
        config = typing.cast(Dict[str, Any], json.load(config_data))

    return config


def contrast_instance_from_json(
    credentials: ContrastAPICredentials,
) -> "ContrastTeamServer":
    return ContrastTeamServer(
        credentials.base_url,
        credentials.api_key,
        _create_authorization_header(credentials),
    )


def _create_authorization_header(credentials: ContrastAPICredentials) -> str:
    """
    Create the Authorization header for the TeamServer API
    """
    unencoded_authorization_header = f"{credentials.username}:{credentials.service_key}"
    encoded_authorization_header = base64.b64encode(
        unencoded_authorization_header.encode("utf-8")
    )
    return encoded_authorization_header.decode("utf-8")


class ContrastTeamServer:

    def __init__(
        self,
        teamserver_url: str,
        api_key: str,
        authorization_header: str,
        application_metadata_field_name: str = "",
    ):
        teamserver_url = teamserver_url.strip()

        regexBaseUrl = "^(http|https):\\/\\/[a-z0-9\\.]*(:)?([0-9]*)"

        if re.match(regexBaseUrl, teamserver_url):
            if re.match(regexBaseUrl + "$", teamserver_url):
                teamserver_url = teamserver_url + "/Contrast/api/ng/"
            elif re.match(regexBaseUrl + "\\/$", teamserver_url):
                teamserver_url = teamserver_url + "Contrast/api/ng/"
            elif re.match(regexBaseUrl + "\\/Contrast$", teamserver_url):
                teamserver_url = teamserver_url + "/api/ng/"
            elif re.match(regexBaseUrl + "\\/Contrast\\/$", teamserver_url):
                teamserver_url = teamserver_url + "api/ng/"
            elif re.match(regexBaseUrl + "\\/Contrast\\/api$", teamserver_url):
                teamserver_url = teamserver_url + "/ng/"
            elif re.match(regexBaseUrl + "\\/Contrast\\/api\\/$", teamserver_url):
                teamserver_url = teamserver_url + "ng/"
            elif re.match(regexBaseUrl + "\\/Contrast\\/api\\/ng$", teamserver_url):
                teamserver_url = teamserver_url + "/"
            elif (
                re.match(regexBaseUrl + "\\/Contrast\\/api\\/ng\\/$", teamserver_url)
                is None
            ):
                raise ValueError("Unrecognised TeamServer URL")

        self._teamserver_url: str = teamserver_url
        self._api_key: str = api_key
        self._authorization_header: str = authorization_header
        self._application_metadata_field_name: str = application_metadata_field_name

        self._is_superadmin: bool = False

        self._title_cwe_cache: Dict[Any, Any] = {}

    @property
    def teamserver_url(self) -> str:
        return self._teamserver_url

    # Function to call the Contrast TeamServer REST API and retrieve results as JSON
    def api_request(self, path: str, api_key: str = "") -> Dict[str, Any]:
        if not api_key:
            api_key = self._api_key

        url = self._teamserver_url + path
        headers = {
            "Accept": "application/json",
            "Api-Key": api_key,
            "Authorization": self._authorization_header,
        }

        try:
            response = httpx.get(url, headers=headers)
            response.raise_for_status()
            data = typing.cast(Dict[str, Any], response.json())
            return data
        except httpx.HTTPStatusError as e:
            print(e)
            raise

    # Function to POST data to the Contrast TeamServer REST API and retrieve results as JSON
    def post_api_request(self, path: str, data: bytes, api_key: str = "") -> bytes:
        if not api_key:
            api_key = self._api_key

        url = self._teamserver_url + path
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Api-Key": api_key,
            "Authorization": self._authorization_header,
        }

        try:
            response = httpx.post(url, headers=headers, content=data)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            print(e)
            raise

    # Superadmin API call to retrieve the API key for a specific organization
    def org_api_key(self, org_id: str) -> Dict[str, str]:
        if self._is_superadmin:
            return self.api_request("superadmin/organizations/" + org_id + "/apiKey")
        else:
            return {"api_key": self._api_key}

    # Organization specific API call to list assess policy (rules)
    def list_org_policy(
        self, org_id: str, api_key: str, expand_apps: bool = False
    ) -> List[Dict[str, Any]]:
        call = org_id + "/rules?expand=skip_links"
        if expand_apps:
            call += ",app_assess_rules"

        rules = typing.cast(
            List[Dict[str, Any]], self.api_request(call, api_key)["rules"]
        )

        return rules

    # Organization specific API call to retrieve CWE ID for a trace. Cache results locally by rule name as a speedup.
    def trace_cwe(self, org_id: str, title: str, api_key: str) -> str:
        if len(self._title_cwe_cache) == 0:
            policies = self.list_org_policy(org_id, api_key)
            for policy in policies:
                self._title_cwe_cache[policy["title"]] = (
                    policy["cwe"].split("/")[-1].replace(".html", "")
                )
        title = typing.cast(str, self._title_cwe_cache[title])
        return title

    def update_rule_references(
        self, org_id: str, rule_name: str, references: List[str], api_key: str
    ) -> bytes:
        values = {"references": references}

        data = json.dumps(values).encode("utf-8")

        response = self.post_api_request(org_id + "/rules/" + rule_name, data, api_key)

        return response

    def send_usage_event(self, org_id: str, is_reset: bool, api_key: str) -> bytes:
        usage_mode_endpoint = "undo" if is_reset else "setup"

        values = {"type": usage_mode_endpoint}

        data = json.dumps(values).encode("utf-8")

        response = self.post_api_request(org_id + "/integrations/diagnostics/scw", data)

        return response
