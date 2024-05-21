## c6t
An unofficial Administrative Command Line Interface for Contrast Security

### Features
- Login to your Contrast account and save your API credentials to your local machine.
- Configure your API credentials manually.
- Download the agent configuration file to your local machine.

### Pre-requisites
- Python 3.8 or higher

### Installation
```shell
$ pip install c6t
```

### Usage
#### Login
This will prompt you to login to your Contrast account and save your API credentials to your local machine.
```shell
$ c6t login
```

#### Configure
Alternatively, you can configure your API credentials manually.
```shell
$ c6t configure
```

#### Get Agent Configuration File
This will download the agent configuration file to your local machine.
```shell
$ c6t get-agent-config
```
