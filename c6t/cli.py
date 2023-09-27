import typer
from typing_extensions import Annotated


from rich import print as rprint

from c6t.configure.credentials import ContrastAPICredentials
from c6t.ui.auth import ContrastUIAuthManager
from c6t.api.agent_config import AgentConfig

app = typer.Typer()


@app.command()
def login(
    profile: Annotated[
        str, typer.Argument(help="profile to use for TeamServer credentials.")
    ] = "default"
) -> None:
    """
    Configure the c6t CLI credentials by logging in to the Contrast platform using your UI credentials.
    If no profile is specified, the default profile will be used.
    You can configure a named profile using the --profile argument.
    If your credentials file does not exist (the default location is ~/.c6t/credentials),
    the c6t CLI will create it for you.
    """
    # Hardcoded for now. TODO: Get from config file
    base_url = "https://eval.contrastsecurity.com/Contrast"
    auth = ContrastUIAuthManager(base_url=base_url)
    auth.login(profile=profile)


@app.command()
def configure(
    profile: Annotated[
        str, typer.Argument(help="profile to use for TeamServer credentials.")
    ] = "default"
) -> None:
    """
    Configure the c6t CLI credentials. If no profile is specified, the default profile will be used.
    You can configure a named profile using the --profile argument.
    If your credentials file does not exist (the default location is ~/.c6t/credentials),
    the c6t CLI will create it for you.
    """
    credentials = ContrastAPICredentials()
    credentials.base_url = typer.prompt("Contrast TeamServer URL")
    credentials.username = typer.prompt("Contrast username")
    credentials.service_key = typer.prompt("Contrast service key")
    credentials.api_key = typer.prompt("Contrast API key")
    credentials.organization_uuid = typer.prompt("Contrast organization UUID")
    credentials.superadmin = typer.confirm("Contrast superadmin status")
    credentials.write_credentials_to_file()


@app.command()
def get_agent_config(
    profile: Annotated[
        str, typer.Argument(help="profile to use for TeamServer credentials.")
    ] = "default",
    path: Annotated[str, typer.Argument()] = "contrast_security.yaml",
    language: Annotated[str, typer.Argument()] = "JAVA",
) -> None:
    """
    Gets the Contrast Agent YAML config file from TeamServer and saves it to the current working directory.
    Alternatively, you can specify a path to save the file to using the --path argument.
    """
    rprint("Getting agent config...")
    agent_config = AgentConfig(profile=profile)
    yaml_text = agent_config.get_agent_credentials(language=language)
    rprint("Writing agent config to file...")
    agent_config.write_agent_config_to_file(path=path, yaml_text=yaml_text)


if __name__ == "__main__":
    app()
