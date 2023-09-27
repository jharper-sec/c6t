import typer

from rich import print as rprint

from c6t.configure.credentials import ContrastAPICredentials
from c6t.ui.auth import ContrastUIAuthManager
from c6t.api.agent_config import AgentConfig

app = typer.Typer()


@app.command()
def login(profile: str = "default") -> None:
    """
    Login to the Contrast platform using your UI credentials (username/password).
    This will automatically configure your API credentials and save them to the
    credentials file.
    """
    # Hardcoded for now. TODO: Get from config file
    base_url = "https://eval.contrastsecurity.com/Contrast"
    auth = ContrastUIAuthManager(base_url=base_url)
    auth.login(profile=profile)


@app.command()
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


@app.command()
def get_agent_config(
    profile: str = "default",
    path: str = "contrast_security.yaml",
    language: str = "JAVA",
) -> None:
    """
    Gets the Contrast Agent YAML config file from TeamServer
    and saves it to the current working directory.
    """
    rprint("Getting agent config...")
    agent_config = AgentConfig(profile=profile)
    yaml_text = agent_config.get_agent_credentials(language=language)
    rprint("Writing agent config to file...")
    agent_config.write_agent_config_to_file(path=path, yaml_text=yaml_text)


if __name__ == "__main__":
    app()
