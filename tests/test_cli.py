import pytest
from typer.testing import CliRunner
from c6t.cli import app

runner = CliRunner()


def test_main_entrypoint() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_download_agent() -> None:
    result = runner.invoke(app, ["download-agent", "--language", "JAVA"])
    assert result.exit_code == 0
    assert "Downloading Contrast agent" in result.output


if __name__ == "__main__":
    pytest.main()
