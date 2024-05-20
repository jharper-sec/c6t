import typer
import yaml
import pathlib
from git.repo import Repo
from jinja2 import Environment, FileSystemLoader

from rich import print as rprint

from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from c6t.configure.credentials import ContrastAPICredentials
from c6t.ui.auth import ContrastUIAuthManager
from c6t.api.agent_config import AgentConfig

from c6t.external.integrations.scw.contrast_scw import scw_create, scw_delete

app = typer.Typer()
integrations_app = typer.Typer()
scw_integration_app = typer.Typer()
app.add_typer(
    integrations_app, name="integrations", help="Integrations with other tools"
)
integrations_app.add_typer(scw_integration_app, name="scw", help="Secure Code Warrior")


@app.command("login")
def login(profile: str = "default") -> None:
    """
    Login to the Contrast platform using your UI credentials (username/password).
    This will automatically configure your API credentials and save them to the
    credentials file.
    """

    contrast_environment = inquirer.select(  # type: ignore
        message="Select your Contrast TeamServer Environment:",
        choices=[
            Choice(
                value="https://cs004.contrastsecurity.com/Contrast", name="Free Trial"
            ),
            Choice(
                value="https://eval.contrastsecurity.com/Contrast", name="Evaluation"
            ),
            Choice(
                value="https://app.contrastsecurity.com/Contrast", name="Enterprise"
            ),
            Choice(value=None, name="Exit"),
        ],
        default="Free Trial",
    ).execute()

    if contrast_environment:
        auth = ContrastUIAuthManager(base_url=contrast_environment)
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
    path: str = "contrast_security.yaml",
    language: str = "JAVA",
) -> None:
    """
    Gets the Contrast Agent YAML config file from TeamServer
    and saves it to the current working directory.
    """

    # Get initials from user input
    initials = typer.prompt("Enter your initials")
    environment = "dev"

    # Attach to repo in current working directory
    repo = Repo(".")

    # Get credentials from file
    rprint("Getting agent config from TeamServer...")
    agent_config = AgentConfig(profile=profile)
    raw_yaml_text = agent_config.get_agent_credentials(language=language)
    credentials = yaml.safe_load(raw_yaml_text).get("api")

    # Load Jinga2 template and render using YAML text
    rprint("Rendering agent config...")
    template_path = pathlib.Path("~/.c6t/templates").expanduser()
    template_loader = FileSystemLoader(searchpath=template_path)
    template_env = Environment(loader=template_loader)
    template = template_env.get_template("contrast_security.yaml.j2")
    rendered_yaml_text = template.render(
        url=credentials.get("url"),
        api_key=credentials.get("api_key"),
        service_key=credentials.get("service_key"),
        user_name=credentials.get("user_name"),
        application_name=f"TerracottaBank-{initials}",
        branch_name=repo.active_branch,
        commit_hash=repo.head.commit,
        committer=repo.head.commit.author,
        repository=repo.remotes.origin.url,
        environment=environment,
    )

    rprint("Writing agent config to file...")
    agent_config.write_agent_config_to_file(path=path, yaml_text=rendered_yaml_text)


# TODO: Add a command to populate vulnerability references with Secure Code Warrior links
@scw_integration_app.command("create")
def scw(profile: str = "default") -> None:
    """
    Populate vulnerability references with Secure Code Warrior links.
    """
    print("Creating SCW links...")
    scw_create(profile=profile)


@scw_integration_app.command("delete")
def scw_reset(profile: str = "default") -> None:
    """
    Delete vulnerability references and reset to the original Contrast links.
    """
    print("Deleting SCW links...")
    scw_delete(profile=profile)


if __name__ == "__main__":
    app()
