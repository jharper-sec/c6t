# c6t

An unofficial Administrative Command Line Interface (CLI) for Contrast Security.

## Table of Contents

- [c6t](#c6t)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Login](#login)
    - [Configure](#configure)
    - [Get Agent Configuration File](#get-agent-configuration-file)
  - [Project Structure](#project-structure)
  - [Development](#development)
    - [Setting Up](#setting-up)
    - [Running Tests](#running-tests)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- Login to your Contrast account and save your API credentials to your local machine.
- Configure your API credentials manually.
- Download the agent configuration file to your local machine.
- Integrate with Secure Code Warrior to fetch training exercises and videos for identified vulnerabilities.
- Download the latest Contrast Security agent from the Maven repository.

## Prerequisites

- Python 3.8 or higher

## Installation

```shell
$ pip install c6t
```

## Usage

### Login

This will prompt you to login to your Contrast account and save your API credentials to your local machine.

```shell
$ c6t login
```

### Configure

Alternatively, you can configure your API credentials manually.

```shell
$ c6t configure
```

### Get Agent Configuration File

This will download the agent configuration file to your local machine.

```shell
$ c6t agent-config
```

## Project Structure

```
c6t-main/
├── .github/               # GitHub configuration files for CI/CD
│   ├── dependabot.yml
│   └── workflows/
│       └── dump-env.yml
├── src/                   # Source files for the c6t package
│   └── c6t/
│       ├── api/
│       │   ├── agent_config.py
│       │   ├── __init__.py
│       │   └── maven_repo.py
│       ├── configure/
│       │   ├── __init__.py
│       │   └── credentials.py
│       ├── external/
│       │   └── integrations/
│       │       └── scw/
│       │           ├── __init__.py
│       │           ├── contrast_api.py
│       │           └── contrast_scw.py
│       ├── templates/
│       │   ├── contrast_security.yaml.j2
│       │   └── contrast_security_env.yaml.j2
│       ├── ui/
│       │   └── auth.py
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
├── tests/                 # Unit tests
│   ├── data/
│   │   ├── checksumfile
│   │   └── testfile
│   ├── __init__.py
│   ├── test_cli.py
│   └── test_maven_repo.py
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml         # Project configuration
├── requirements-dev.lock
└── requirements.lock
```

## Development

### Setting Up

1. Clone the repository:
    ```shell
    $ git clone https://github.com/jharper-sec/c6t
    $ cd c6t
    ```

2. Install [Rye](https://rye.astral.sh/):
    Linux/macOS:
    ```shell
    $ curl -sSf https://rye.astral.sh/get | bash
    ```

3. Use Rye to install the dependencies:
    ```shell
    $ rye sync
    ```

### Running Tests

To run the tests, use:

```shell
$ rye run pytest
```

## Contributing

Contributions are welcome! Please read the [contributing guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the terms of the Apache license. See the [LICENSE](LICENSE) file for details.
