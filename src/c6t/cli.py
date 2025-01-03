from typing import Optional
from pathlib import Path
import sys

import typer
import yaml
from git.repo import Repo
from git.exc import InvalidGitRepositoryError
from jinja2 import Environment, PackageLoader

from rich import print as rprint

import questionary

from c6t.configure.credentials import ContrastAPICredentials
from c6t.ui.auth import ContrastUIAuthManager
from c6t.api.agent_config import AgentConfig
from c6t.api.applications import Applications
from c6t.api import maven_repo
from c6t.external.integrations.scw.contrast_scw import scw_create, scw_delete
from c6t.tools.udp_server import start_udp_server
from c6t.tools.send_udp_test_message import (
    SyslogFacility,
    SyslogSeverity,
    send_udp_test_message,
)

app = typer.Typer()
integrations_app = typer.Typer()
scw_integration_app = typer.Typer()
tools = typer.Typer()
app.add_typer(
    integrations_app, name="integrations", help="Integrations with other tools"
)
integrations_app.add_typer(scw_integration_app, name="scw", help="Secure Code Warrior")
app.add_typer(tools, name="tools", help="Additional tools")


@app.command("login")
def login(
    profile: str = "default",
    username: Optional[str] = None,
    password: Optional[str] = None,
    environment: Optional[str] = None,
    url: Optional[str] = None,
    organization_uuid: Optional[str] = None,
) -> None:
    """
    Login to the Contrast platform using your UI credentials (username/password).
    This will automatically configure your API credentials and save them to the
    credentials file.

    Args:
        profile: The credentials profile to use (default: "default")
        username: Contrast username (optional)
        password: Contrast password (optional)
        environment: Contrast environment - "trial", "eval", or "enterprise" (optional)
        url: Custom Contrast TeamServer URL for enterprise installations (optional)
        organization_uuid: Specific organization UUID to use (optional)
    """
    contrast_environment = None
    
    if environment:
        environment = environment.lower()
        if environment == "trial":
            contrast_environment = "https://cs004.contrastsecurity.com/Contrast"
        elif environment == "eval":
            contrast_environment = "https://eval.contrastsecurity.com/Contrast"
        elif environment == "enterprise":
            contrast_environment = url if url else questionary.text(
                "Enter your Contrast TeamServer URL:"
            ).ask()
    
    if not contrast_environment:
        contrast_environment = questionary.select(
            "Select your Contrast TeamServer Environment:",
            choices=[
                {
                    "name": "Free Trial",
                    "value": "https://cs004.contrastsecurity.com/Contrast",
                },
                {
                    "name": "Evaluation",
                    "value": "https://eval.contrastsecurity.com/Contrast",
                },
                {"name": "Enterprise", "value": "Enterprise"},
            ],
            default={
                "name": "Free Trial",
                "value": "https://cs004.contrastsecurity.com/Contrast",
            },
        ).ask()

        if contrast_environment == "Enterprise":
            contrast_environment = questionary.text(
                "Enter your Contrast TeamServer URL:"
            ).ask()

    if contrast_environment:
        auth = ContrastUIAuthManager(base_url=contrast_environment)
        # Pre-set the credentials if provided
        if username:
            auth.ui_credentials.username = username
        if password:
            auth.ui_credentials.password = password
        if organization_uuid:
            auth.organization_uuid = organization_uuid
        auth.login(profile=profile)

@app.command("configure")
def configure(profile: str = "default") -> None:
    """
    Configure the c6t CLI credentials.
    This will save your credentials to the credentials file.
    """
    credentials = ContrastAPICredentials()
    credentials.profile = profile
    credentials.base_url = typer.prompt("Contrast TeamServer URL")
    credentials.username = typer.prompt("Contrast username")
    credentials.service_key = typer.prompt("Contrast service key")
    credentials.api_key = typer.prompt("Contrast API key")
    credentials.organization_uuid = typer.prompt("Contrast organization UUID")
    credentials.superadmin = typer.confirm("Contrast superadmin status")
    credentials.write_credentials_to_file()


@app.command("agent-config")
def agent_config(
    profile: str = "default",
    type: str = "yaml",
    path: Optional[str] = None,
    application_name: Optional[str] = None,
    application_group: Optional[str] = None,
    environment: str = "dev",
    language: str = "JAVA",
    include_credentials: bool = True,
) -> None:
    """
    Gets the Contrast Agent YAML config file from TeamServer
    and saves it to the current working directory.
    """

    branch_name: Optional[str] = None
    commit_hash: Optional[str] = None
    committer: Optional[str] = None
    repository: Optional[str] = None

    # Attach to repo in current working directory
    try:
        repo = Repo(".")
        branch_name = str(repo.active_branch)
        commit_hash = str(repo.head.commit)
        committer = str(repo.head.commit.author)
        repository = str(repo.remotes.origin.url)
    except InvalidGitRepositoryError:
        rprint("This command must be run in a git repository.")

    # Get credentials from file
    rprint("Getting agent config from TeamServer...")
    agent_config = AgentConfig(profile=profile)
    raw_yaml_text = agent_config.get_agent_credentials(language=language)
    credentials = yaml.safe_load(raw_yaml_text).get("api")

    # Load Jinga2 template and render using YAML text
    rprint("Rendering agent config...")
    template_env = Environment(
        loader=PackageLoader("c6t", "templates"),
        autoescape=True,
    )

    yaml_template = template_env.get_template("contrast_security.yaml.j2")
    env_template = template_env.get_template("contrast_security_env.yaml.j2")

    rendered_yaml_text = yaml_template.render(
        url=credentials.get("url"),
        api_key=credentials.get("api_key"),
        service_key=credentials.get("service_key"),
        user_name=credentials.get("user_name"),
        application_name=application_name,
        application_group=application_group,
        branch_name=branch_name,
        commit_hash=commit_hash,
        committer=committer,
        repository=repository,
        environment=environment,
        include_credentials=include_credentials,
    )

    rendered_env_text = env_template.render(
        url=credentials.get("url"),
        api_key=credentials.get("api_key"),
        service_key=credentials.get("service_key"),
        user_name=credentials.get("user_name"),
        application_name=application_name,
        application_group=application_group,
        branch_name=branch_name,
        commit_hash=commit_hash,
        committer=committer,
        repository=repository,
        environment=environment,
        include_credentials=include_credentials,
    )

    rprint("Writing agent config to file...")
    if type == "yaml":
        if path is None:
            path = "contrast_security.yaml"
        agent_config.write_agent_config_to_file(path=path, text=rendered_yaml_text)
        rprint(f"Validating agent config file at {path}...")
        valid = agent_config.validate_agent_config_file_is_valid_yaml(path=path)
        if valid:
            rprint(f"[green]Agent config file at {path} is valid")
        else:
            rprint(f"[red]Agent config file at {path} is invalid")
            sys.exit(1)

    elif type == "env":
        if path is None:
            path = "contrast.env"
        agent_config.write_agent_config_to_file(path=path, text=rendered_env_text)


@app.command("reset-application")
def reset_application(
    app_name: str,
    profile: str = "default",
) -> None:
    """
    Reset the application to its original state.
    """
    rprint("Resetting application...")

    applications = Applications(profile=profile)
    app_id = applications.get_app_id_from_name(app_name)
    message = applications.reset_application(app_id)
    rprint(message)


@app.command("download-agent")
def download_agent(
    language: str = "JAVA",
    repository_url: str = "https://repo1.maven.org/maven2",
    version: str = "latest",
    target_dir: Path = Path("."),
) -> None:
    """
    Download the Contrast agent for the specified language.
    """

    MAVEN_PACKAGE_NAMESPACE = "com/contrastsecurity/contrast-agent"

    if language == "JAVA":
        rprint(f"Downloading Contrast agent ({version})...")
        downloader = maven_repo.FileDownloader()
        verifier = maven_repo.ChecksumVerifier()
        metadata_handler = maven_repo.MavenMetadataHandler(
            downloader=downloader, namespace=MAVEN_PACKAGE_NAMESPACE
        )
        agent_downloader = maven_repo.JavaAgentDownloader(
            downloader=downloader, verifier=verifier, metadata_handler=metadata_handler
        )

        agent_downloader.download_agent(repository_url, version, target_dir)

    else:
        rprint("Unsupported language")


@scw_integration_app.command("create")
def scw(profile: str = "default") -> None:
    """
    Populate vulnerability references with Secure Code Warrior links.
    """
    rprint("Creating SCW links...")
    scw_create(profile=profile)


@scw_integration_app.command("delete")
def scw_reset(profile: str = "default") -> None:
    """
    Delete vulnerability references and reset to the original Contrast links.
    """
    rprint("Deleting SCW links...")
    scw_delete(profile=profile)


@tools.command("udp-server")
def udp_server(
    udp_ip: str = "127.0.0.1",
    udp_port: int = 10514,
    forward_ip: Optional[str] = None,
    forward_port: Optional[int] = None,
) -> None:
    """
    Start a UDP server to receive Contrast agent syslog messages.
    """

    start_udp_server(udp_ip, udp_port, forward_ip, forward_port)


@tools.command("send-udp-message")
def send_udp_message(
    udp_ip: str = "127.0.0.1",
    udp_port: int = 10514,
    syslog_facility: int = SyslogFacility.LOCAL3.value,
    syslog_severity: int = SyslogSeverity.INFO.value,
    message: str = "Test message from c6t.",
) -> None:
    """
    Send a UDP message to the specified IP and port.
    """
    send_udp_test_message(
        udp_ip=udp_ip,
        udp_port=udp_port,
        syslog_facility=syslog_facility,
        syslog_severity=syslog_severity,
        message=message,
    )


if __name__ == "__main__":
    app()
