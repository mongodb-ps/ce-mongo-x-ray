# x-ray
[![Makefile](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml)
[![Release](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/mongo-x-ray.svg)](https://pypi.org/project/mongo-x-ray/)


This project aims to create tools for MongoDB analysis and diagnosis.

See [How to Install](#1-how-to-install) below.

## 1 How to Install
### 1.1 PyPi
#### 1.1.1 Install with Pip
The easiest and recommended way to install x-ray is to use `pip`:
```bash
pip install mongo-x-ray
```

#### 1.1.2 Build from Source
```bash
git clone https://github.com/mongodb-ps/ce-mongo-x-ray
cd ce-mongo-x-ray
pip install .
```

### 1.2 PyInstaller
#### 1.2.1 Prebuilt Binaries
Currently the prebuilt binaries are available on 3 platforms:
- Ubuntu 22.04 (AMD64)
- MacOS 14 (ARM64)
- Windows 2022 (AMD64)

Download them from [Releases](https://github.com/mongodb-ps/ce-mongo-x-ray/releases).

#### 1.2.2 Build from Source
x-ray is tested on `Python 3.9.22`. On MacOS or Linux distributions, you can use the `make` command to build the binary:
```bash
git clone https://github.com/mongodb-ps/ce-mongo-x-ray
cd ce-mongo-x-ray
make deps # if it's the first time you build the project
make # equal to `make build`
```

There are other make targets. Use `make help` to find out.

For Windows users, if `make` command is not available. You can use Python commands to build the binary:
```powershell
python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m PyInstaller --onefile `
  --name x-ray `
  --add-data="templates;templates" `
  --add-data="libs;libs" `
  --icon="misc/x-ray.ico" `
  --hidden-import=openai `
  x-ray
```

#### 1.3 For Developers
For developers, use `make deps` to prepare venv and dependencies
```bash
make deps
```
Or
```bash
python3 -m venv .venv
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

Useful development targets (see `make help`):
- `make unit-test` — run the unit tests in the core and every local plugin checkout under `plugins/`.
- `make lint` — ruff check + ruff format --check.
- `make minify` — minify the HTML/JS/CSS templates.

## 2 Using the Tool
```bash
x-ray [-h] [-q] [-c CONFIG] {log,gmd,healthcheck,ftdc}
```
Run `x-ray --help` to see the commands available in your environment.
| Argument         | Description                                                                                                                                                                                                                                     |        Default         |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------: |
| `-q`, `--quiet`  | Quiet mode.                                                                                                                                                                                                                                     |        `false`         |
| `-h`, `--help`   | Show the help message and exit.                                                                                                                                                                                                                 |          n/a           |
| `-c`, `--config` | Path to configuration file.                                                                                                                                                                                                                     | Built-in `config.json` |
| `command`        | Command to run:<br/>- `log`: Log analysis.<br/>- `ftdc`: FTDC analysis.<br/>- `gmd`: getMongoData analysis.<br/>- `healthcheck` (`hc`): deployment health check. |          None          |

Besides, you can use environment variables to control some behaviors:
- `ENV=development` For developing. It will change the following behaviors:
  - Formatted the output JSON for for easier reading.
  - The output will not create a new folder for each run but overwrite the same files.
- `LOG_LEVEL`: Can be `DEBUG`, `ERROR` or `INFO` (default).

