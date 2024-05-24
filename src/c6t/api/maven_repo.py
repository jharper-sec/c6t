import hashlib
from io import BytesIO
from pathlib import Path
from typing import Any
import shutil
import tempfile

import requests
from rich.progress import Progress
from rich import print as rprint
from lxml import etree

session = requests.Session()


def verify_file_checksum(
    target_filename: Path, checksum_filename: Path, algorithm: str
) -> bool:
    """
    Verify the checksum of a file against a checksum file.
    """
    rprint(f"[cyan]Verifying checksum for {target_filename.name}...")
    with open(target_filename, "rb") as f:
        target_checksum = hashlib.new(
            algorithm, f.read(), usedforsecurity=True
        ).hexdigest()
    with open(checksum_filename, "r") as f:
        checksum = f.read().strip()
    if target_checksum != checksum:
        raise ValueError(f"Checksum does not match for {target_filename.name}.")
    else:
        rprint(f"[green]Checksum verified for {target_filename.name}.")
    return True


def download_file(url: str, filename: Path) -> None:
    rprint(f"[cyan]Starting download from: {url}")
    with Progress() as progress:
        task = progress.add_task(f"[cyan]Downloading...", total=100)
        response = session.get(url, stream=True)
        response.raise_for_status()
        total_length = int(response.headers.get("content-length", 0))
        chunk_size = 4096

        with open(filename, "wb") as f:
            for data in response.iter_content(chunk_size=chunk_size):
                f.write(data)
                progress.update(task, advance=len(data) / total_length * 100)
    rprint(f"[green]Download completed: {filename.name}")


def download_maven_metadata_from_repo(repository_url: str, temp_dir: Path) -> Path:
    url = f"{repository_url}/com/contrastsecurity/contrast-agent/maven-metadata.xml"
    filename = temp_dir / "maven-metadata.xml"
    download_file(url, filename)
    return filename


def download_maven_metadata_checksum_from_repo(
    repository_url: str, algorithm: str, temp_dir: Path
) -> Path:
    filename = temp_dir / f"maven-metadata.xml.{algorithm}"
    url = f"{repository_url}/com/contrastsecurity/contrast-agent/{filename.name}"
    download_file(url, filename)
    return filename


def parse_maven_metadata(metadata_file: Path) -> Any:
    with open(metadata_file, "r") as f:
        metadata = f.read()
    tree = etree.parse(BytesIO(metadata.encode("utf-8")))
    return tree.getroot()


def get_latest_version_from_maven_metadata(root: Any) -> str:
    versioning = root.find("versioning")
    if versioning is not None:
        latest = versioning.find("latest")
        if latest is not None:
            if latest.text is not None:
                return latest.text.strip()
    raise ValueError("Could not find latest version in Maven metadata.")


def is_version_in_maven_metadata(root: Any, version: str) -> bool:
    versioning = root.find("versioning")
    if versioning is not None:
        versions = versioning.find("versions")
        if versions is not None:
            for v in versions:
                if v.text is not None and v.text.strip() == version:
                    return True
    raise ValueError(f"Version {version} is not in Maven metadata.")


def download_java_agent_from_repo(
    repository_url: str, version: str, target_dir: Path
) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        maven_metadata_file = download_maven_metadata_from_repo(
            repository_url, temp_dir_path
        )
        maven_metadata_checksum_file = download_maven_metadata_checksum_from_repo(
            repository_url, "sha1", temp_dir_path
        )
        verify_file_checksum(maven_metadata_file, maven_metadata_checksum_file, "sha1")

        root = parse_maven_metadata(maven_metadata_file)

        if version == "latest":
            version = get_latest_version_from_maven_metadata(root)
        else:
            if not is_version_in_maven_metadata(root, version):
                raise ValueError(f"Version {version} is not in Maven metadata.")

        jar_filename = temp_dir_path / "contrast.jar"
        url = f"{repository_url}/com/contrastsecurity/contrast-agent/{version}/contrast-agent-{version}.jar"
        download_file(url, jar_filename)
        java_agent_checksum_filename = download_java_agent_checksum_from_repo(
            repository_url, version, temp_dir_path
        )
        verify_file_checksum(jar_filename, java_agent_checksum_filename, "sha1")

        target_jar_path = target_dir / "contrast.jar"
        shutil.copy(jar_filename, target_jar_path)
        rprint(f"[green]File copied to {target_jar_path}")

    return target_jar_path


def download_java_agent_checksum_from_repo(
    repository_url: str, version: str, temp_dir: Path, algorithm: str = "sha1"
) -> Path:
    if version == "latest":
        version = get_latest_version_from_maven_metadata(
            parse_maven_metadata(temp_dir / "maven-metadata.xml")
        )

    java_agent_checksum_filename = (
        temp_dir / f"contrast-agent-{version}.jar.{algorithm}"
    )
    url = f"{repository_url}/com/contrastsecurity/contrast-agent/{version}/{java_agent_checksum_filename.name}"
    download_file(url, java_agent_checksum_filename)
    return java_agent_checksum_filename
