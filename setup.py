from setuptools import setup

setup(
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
    entry_points={
        "console_scripts": ['c6t = c6t.__main__:main']
    },
)
