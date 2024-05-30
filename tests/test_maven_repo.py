import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from lxml import etree

from c6t.api.maven_repo import (
    ChecksumVerifier,
    FileDownloader,
    MavenMetadataHandler,
    JavaAgentDownloader,
)

MAVEN_PACKAGE_NAMESPACE = "com/contrastsecurity/contrast-agent"


@pytest.fixture
def mock_downloader() -> MagicMock:
    return MagicMock(spec=FileDownloader)


@pytest.fixture
def mock_verifier() -> MagicMock:
    return MagicMock(spec=ChecksumVerifier)


@pytest.fixture
def mock_metadata_handler(mock_downloader: MagicMock) -> MavenMetadataHandler:
    return MavenMetadataHandler(mock_downloader, MAVEN_PACKAGE_NAMESPACE)


@pytest.fixture
def agent_downloader(
    mock_downloader: MagicMock,
    mock_verifier: MagicMock,
    mock_metadata_handler: MagicMock,
) -> JavaAgentDownloader:
    return JavaAgentDownloader(mock_downloader, mock_verifier, mock_metadata_handler)


def test_verify_file_checksum_success(mock_verifier: MagicMock) -> None:
    mock_verifier.verify_file_checksum.return_value = True
    result = ChecksumVerifier.verify_file_checksum(
        Path("tests/data/testfile"), Path("tests/data/checksumfile"), "sha1"
    )
    assert result is True


def test_download_file(mock_downloader: MagicMock) -> None:
    url = "https://example.com/file"
    filename = Path("/path/to/file")
    mock_downloader.download_file(url, filename)
    mock_downloader.download_file.assert_called_once_with(url, filename)


def test_parse_maven_metadata(mock_metadata_handler: MagicMock) -> None:
    metadata_content = """<metadata>
                            <versioning>
                                <latest>1.2.3</latest>
                            </versioning>
                          </metadata>"""
    with patch("builtins.open", mock_open(read_data=metadata_content)):
        root = mock_metadata_handler.parse_maven_metadata(Path("metadata.xml"))
        versioning = root.find("versioning")
        assert versioning is not None
        assert versioning.find("latest").text == "1.2.3"


def test_get_latest_version(mock_metadata_handler: MagicMock) -> None:
    root = etree.Element("metadata")
    versioning = etree.SubElement(root, "versioning")
    latest = etree.SubElement(versioning, "latest")
    latest.text = "1.2.3"
    version = mock_metadata_handler.get_latest_version(root)
    assert version == "1.2.3"


def test_is_version_in_metadata(mock_metadata_handler: MagicMock) -> None:
    root = etree.Element("metadata")
    versioning = etree.SubElement(root, "versioning")
    versions = etree.SubElement(versioning, "versions")
    version = etree.SubElement(versions, "version")
    version.text = "1.2.3"
    assert mock_metadata_handler.is_version_in_metadata(root, "1.2.3") is True


def test_download_agent(
    agent_downloader: MagicMock,
    mock_metadata_handler: MagicMock,
    mock_verifier: MagicMock,
    mock_downloader: MagicMock,
) -> None:
    repository_url = "https://example.com/maven-repo"
    version = "latest"
    target_dir = Path("/path/to/target/dir")

    # Mocking temporary directory
    with patch("tempfile.TemporaryDirectory") as mock_temp_dir:
        mock_temp_dir_instance = MagicMock()
        mock_temp_dir.return_value = mock_temp_dir_instance
        mock_temp_dir_instance.__enter__.return_value = Path("/temp/dir")

        # Mock the open function for writing files
        with patch("builtins.open", mock_open()) as _:
            # Mock the download and verification steps
            with patch.object(
                mock_metadata_handler,
                "download_maven_metadata",
                return_value=Path("/temp/dir/maven-metadata.xml"),
            ):
                with patch.object(
                    mock_metadata_handler,
                    "download_maven_metadata_checksum",
                    return_value=Path("/temp/dir/maven-metadata.xml.sha1"),
                ):
                    with patch.object(
                        mock_metadata_handler,
                        "parse_maven_metadata",
                        return_value=etree.Element("root"),
                    ):
                        with patch.object(
                            mock_metadata_handler,
                            "get_latest_version",
                            return_value="1.2.3",
                        ):
                            mock_downloader.download_file.return_value = None
                            mock_verifier.verify_file_checksum.return_value = True

                            # Mock shutil.copy to avoid actual file operations
                            with patch("shutil.copy") as mock_copy:
                                result = agent_downloader.download_agent(
                                    repository_url, version, target_dir
                                )
                                assert result == target_dir / "contrast.jar"
                                mock_downloader.download_file.assert_called()
                                mock_verifier.verify_file_checksum.assert_called()
                                mock_copy.assert_called_once_with(
                                    Path("/temp/dir/contrast.jar"),
                                    target_dir / "contrast.jar",
                                )
