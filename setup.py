#!/usr/bin/env python

import setuptools
import importlib.resources as pkg_resources
import pathlib
import shutil


def setup_templates() -> None:
    create_folder_structure()
    copy_templates()


def create_folder_structure() -> None:
    pathlib.Path("~/.c6t/templates").expanduser().mkdir(parents=True, exist_ok=True)


def copy_templates() -> None:
    template_src_dir = pkg_resources.files("c6t").joinpath("templates")
    template_dst_dir = pathlib.Path("~/.c6t/templates").expanduser()
    for template in template_src_dir.iterdir():
        shutil.copy(str(template), str(template_dst_dir))


def setup() -> None:
    setuptools.setup(
        name="c6t",
        version="0.0.1",
        description="Unofficial Contrast CLI",
        url="https//github.com/jharper-sec/c6t",
        author="Jonathan Harper",
        author_email="jonathan.harper@contrastsecurity.com",
        license="Apache 2.0",
        packages=["c6t"],
        zip_safe=False,
        install_requires=[
            "typer[all]",
            "rich",
            "shellingham",
            "requests",
            "annotated-types",
            "types-requests",
            "types-setuptools",
            "jinja2",
            "pyyaml",
            "gitpython",
        ],
        entry_points={"console_scripts": ["c6t = c6t.__main__:main"]},
    )


if __name__ == "__main__":
    setup()
    setup_templates()
