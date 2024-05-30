# Contributing to c6t

Thank you for considering contributing to the c6t project! We welcome contributions of all kinds, including bug fixes, feature enhancements, documentation improvements, and more.

## Table of Contents

- [Contributing to c6t](#contributing-to-c6t)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
  - [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Features](#suggesting-features)
    - [Submitting Pull Requests](#submitting-pull-requests)
  - [Development](#development)
    - [Setting Up](#setting-up)
    - [Running Tests](#running-tests)
  - [Style Guide](#style-guide)
  - [License](#license)

## Getting Started

1. Fork the repository.
2. Clone your fork:

    ```shell
    $ git clone <your-fork-url>
    $ cd c6t-main
    ```

3. Install [Rye](https://rye.astral.sh/) if you haven't already:

    ```shell
    $ curl -sSf https://rye.astral.sh/get | bash
    ```

4. Install the project dependencies:

    ```shell
    $ rye sync
    ```

## How to Contribute

### Reporting Bugs

If you find a bug, please report it by creating an issue in the GitHub repository. Provide as much detail as possible, including steps to reproduce the issue, your environment, and any relevant logs or screenshots.

### Suggesting Features

We welcome feature suggestions! Please open an issue to discuss the feature before starting work on it. This helps ensure that the feature is aligned with the project goals and avoids duplicate efforts.

### Submitting Pull Requests

1. Create a new branch for your work:

    ```shell
    $ git checkout -b feature/your-feature-name
    ```

2. Make your changes and commit them with clear and concise commit messages.

3. Push your branch to your fork:

    ```shell
    $ git push origin feature/your-feature-name
    ```

4. Open a pull request against the `main` branch of the original repository. Provide a clear description of your changes and any additional context that might be helpful.

## Development

### Setting Up

1. Clone the repository:

    ```shell
    $ git clone <repository-url>
    $ cd c6t-main
    ```

2. Install Rye:

    ```shell
    $ curl -sSf https://rye.astral.sh/get | bash
    ```

3. Install the dependencies:

    ```shell
    $ rye sync
    ```

### Running Tests

To run the tests, use:

```shell
$ rye run pytest
```

## Style Guide

- Follow PEP 8 guidelines for Python code.
- Use meaningful variable and function names.
- Write docstrings for all functions, classes, and modules.
- Ensure your code is well-documented and includes comments where necessary.

## License

By contributing to this project, you agree that your contributions will be licensed under the [Apache License](LICENSE).

Thank you for contributing!
