# x-ray
[![Makefile](https://github.com/zhangyaoxing/x-ray/actions/workflows/makefile.yml/badge.svg)](https://github.com/zhangyaoxing/x-ray/actions/workflows/makefile.yml)
[![Release](https://github.com/zhangyaoxing/x-ray/actions/workflows/release.yml/badge.svg)](https://github.com/zhangyaoxing/x-ray/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/mongo-x-ray.svg)](https://pypi.org/project/mongo-x-ray/)


This project aims to create tools for MongoDB analysis and diagnosis. So far 3 modules are being built:
- Health check module.
- Log analysis module.
- `getMongoData` visualization module (Under construction).

## 1 Compatibility Matrix
### Health Check
|  Replica Set  | Sharded Cluster | Standalone |
| :-----------: | :-------------: | :--------: |
| >=4.2 &check; |  >=4.2 &check;  |  &cross;   |

Older versions are not tested.

### Log Analysis
Log analysis requires JSON format logs, which is supported since 4.4.
|  Replica Set  | Sharded Cluster |  Standalone   |
| :-----------: | :-------------: | :-----------: |
| >=4.4 &check; |  >=4.4 &check;  | >=4.4 &check; |

## 2 How to Install
### 2.1 PyPi
#### 2.1.1 Install with Pip
The easiest and recommended way to install x-ray is to use `pip`:
```bash
pip install mongo-x-ray
```

#### 2.1.2 Build from Source
```bash
git clone https://github.com/zhangyaoxing/x-ray
cd x-ray
pip install .
```

### 2.2 PyInstaller
#### 2.2.1 Prebuilt Binaries
Currently the prebuilt binaries are available on 3 platforms:
- Ubuntu 22.04 (AMD64)
- MacOS 14 (ARM64)
- Windows 2022 (AMD64)

Download them from [Releases](https://github.com/zhangyaoxing/x-ray/releases).

#### 2.2.2 Build from Source
x-ray is tested on `Python 3.9.22`. On MacOS or Linux distributions, you can use the `make` command to build the binary:
```bash
git clone https://github.com/zhangyaoxing/x-ray
cd x-ray
make deps # if it's the first time you build the project
make # equal to `make build` and `make build-lite`
```

There are other make targets. Use `make help` to find out.

You can also build the tool with AI modules for log analysis. For more details refer to: [Build with AI Support](https://github.com/zhangyaoxing/x-ray/wiki/Build-with-AI-Support).

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

#### 2.3 For Developers
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

## 3 Using the Tool
```bash
x-ray [-h] [-q] [-c CONFIG] {healthcheck,hc,log}
```
| Argument         | Description                                                                                                                        |           Default           |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------- | :-------------------------: |
| `-q`, `--quiet`  | Quiet mode.                                                                                                                        |           `false`           |
| `-h`, `--help`   | Show the help message and exit.                                                                                                    |             n/a             |
| `-c`, `--config` | Path to configuration file.                                                                                                        | Built-in `libs/config.json` |
| `command`        | Command to run. Include:<br/>- `healthcheck` or `hc`: Health check.<br/>- `log`: Log analysis.<br/>- `version`: Show version info. |            None             |

Besides, you can use environment variables to control some behaviors:
- `ENV=development` For developing. It will change the following behaviors:
  - Formatted the output JSON for for easier reading.
  - The output will not create a new folder for each run but overwrite the same files.
- `LOG_LEVEL`: Can be `DEBUG`, `ERROR` or `INFO` (default).

### 3.1 Health Check Component
#### 3.1.1 Examples
```bash
./x-ray healthcheck localhost:27017 # Scan the cluster with default settings.
./x-ray hc localhost:27017 --output ./output/ # Specify output folder.
./x-ray hc localhost:27017 --config ./config.json # Use your own configuration.
```

#### 3.1.2 Full Arguments
```bash
x-ray healthcheck [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html}] [uri]
```
| Argument           | Description                                 |  Default  |
| ------------------ | ------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                            | `default` |
| `-o`, `--output`   | Output folder path.                         | `output/` |
| `-f`, `--format`   | Output format. Can be `markdown` or `html`. |  `html`   |
| `uri`              | MongoDB database URI.                       |   None    |

For security reasons you may not want to include credentials in the command. There are 2 options:
- If the URI is not provided, user will be asked to input one.
- If URI is provided but not username/password, user will also be asked to input them.

#### 3.1.3 More Info
Refer to the wiki for more details.
- [Customize the thresholds](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Configuration)
- [Database permissions](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Database-Permissions)
- [Output](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Output)
- [Customize the output](https://github.com/zhangyaoxing/x-ray/wiki/Health-Check-Output-Template)

### 3.2 Log Analysis Component
#### 3.2.1 Examples
```bash
# Full analysis
./x-ray log mongodb.log
# For large logs, analyze a random 10% logs
./x-ray log -r 0.1 mongodb.log
```

#### 3.2.2 Full Arguments
```bash
x-ray log [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html}] [log_file]
```
| Argument           | Description                                       |  Default  |
| ------------------ | ------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                  | `default` |
| `-o`, `--output`   | Output folder path.                               | `output/` |
| `-f`, `--format`   | Output format. Can be `markdown` or `html`.       |  `html`   |
| `-r`, `--rate`     | Sample rate. Only analyze a subset of logs.       |    `1`    |
| `--top`            | When analyzing the slow queries, only list top N. |   `10`    |
