# x-ray
[![Makefile](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml)
[![Release](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/mongo-x-ray.svg)](https://pypi.org/project/mongo-x-ray/)


This project aims to create tools for MongoDB analysis and diagnosis.

See [How to Install](#2-how-to-install) below.

## 1 Compatibility Matrix
### 1.1 Log Analysis
Log analysis requires JSON format logs, supported on MongoDB 5.0 and above.
|  Replica Set  | Sharded Cluster |  Standalone   |
| :-----------: | :-------------: | :-----------: |
| >=5.0 &check; |  >=5.0 &check;  | >=5.0 &check; |


### 1.2 FTDC Analysis
Run a basic FTDC analysis, supported on MongoDB 5.0 and above.
|  Replica Set  | Sharded Cluster |  Standalone   |
| :-----------: | :-------------: | :-----------: |
| >=5.0 &check; |  >=5.0 &check;  | >=5.0 &check; |

## 2 How to Install
### 2.1 PyPi
#### 2.1.1 Install with Pip
The easiest and recommended way to install x-ray is to use `pip`:
```bash
pip install mongo-x-ray
```

#### 2.1.2 Build from Source
```bash
git clone https://github.com/mongodb-ps/ce-mongo-x-ray
cd ce-mongo-x-ray
pip install .
```

### 2.2 PyInstaller
#### 2.2.1 Prebuilt Binaries
Currently the prebuilt binaries are available on 3 platforms:
- Ubuntu 22.04 (AMD64)
- MacOS 14 (ARM64)
- Windows 2022 (AMD64)

Download them from [Releases](https://github.com/mongodb-ps/ce-mongo-x-ray/releases).

#### 2.2.2 Build from Source
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

Useful development targets (see `make help`):
- `make unit-test` — run the unit tests in the core and every local plugin checkout under `plugins/`.
- `make lint` — ruff check + ruff format --check.
- `make minify` — minify the HTML/JS/CSS templates.

## 3 Using the Tool
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

### 3.1 Log Analysis Component
#### 3.1.1 Examples
```bash
# Full analysis
./x-ray log mongodb.log
# Time range filter
./x-ray log /var/log/mongodb/ 2026-07-20T08:00:00Z 2026-07-20T10:00:00Z
# For large logs, analyze a random 10% logs
./x-ray log -r 0.1 mongodb.log
# Discover log folders recursively
./x-ray log --discover /var/log/
```

#### 3.1.2 Full Arguments
```bash
x-ray log [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] [-r RATE] [--top TOP] [--discover] log_file [start_time] [end_time]
```
| Argument           | Description                                                                       |  Default  |
| ------------------ | --------------------------------------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                                                  | `default` |
| `-o`, `--output`   | Output folder path.                                                               | `output/` |
| `-f`, `--format`   | Output format (`markdown`, `html`, or `pdf`). PDF also retains Markdown and HTML. |  `html`   |
| `-r`, `--rate`     | Sample rate. Only analyze a subset of logs.                                       |    `1`    |
| `--top`            | When analyzing the slow queries, only list top N.                                 |   `10`    |
| `--discover`       | Recursively search the given path for folders containing log files.               |  `false`  |
| `log_file`         | Path to the MongoDB log file or a folder of log files to analyze.                 |    n/a    |
| `start_time`       | Inclusive UTC start time in ISO-8601 format. Defaults to the first log line.      |    n/a    |
| `end_time`         | Inclusive UTC end time in ISO-8601 format. Defaults to the last log line.         |    n/a    |

### 3.2 FTDC Analysis Component

The FTDC baseline analysis reports its capture timespan and effective sample rate, then
groups metrics into Workload, Read/Write Operations and Latencies, and
Performance sections. It includes operation rates and latencies, host memory
and CPU utilization, WiredTiger cache utilization, queue depth for each block
device, and free-space and utilization charts for every reported mount point.
Each metric shows its peak, average, unit, and a chart saved under the report
output's `charts` directory.
Start and end are inclusive UTC ISO-8601 timestamps. When omitted, the first
and last data points in the archive are used.

```bash
x-ray ftdc /var/lib/mongo/diagnostic.data
x-ray ftdc /var/lib/mongo/diagnostic.data 2026-06-17T08:00:00Z 2026-06-17T10:00:00Z
# Discover FTDC folders recursively
x-ray ftdc --discover /data/
```

```bash
x-ray ftdc [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] [-r RATE] [--svg] [--discover] ftdc_path [start_time] [end_time]
```
| Argument           | Description                                                          |        Default         |
| ------------------ | -------------------------------------------------------------------- | :--------------------: |
| `-s`, `--checkset` | Checkset to run.                                                     |       `default`        |
| `-o`, `--output`   | Output folder path.                                                  |       `output/`        |
| `-r`, `--rate`     | Controls FTDC sampling and accepts a value between `0` and `1`.      |  `1 / ingested files`  |
| `-f`, `--format`   | Output format (`markdown`, `html` or `pdf`). PDF also retains HTML.  |         `html`         |
| `--svg`            | Reference SVG charts instead of converting to PNG.                   |        `false`         |
| `--discover`       | Recursively search the given path for folders containing FTDC files. |        `false`         |
| `ftdc_path`        | Path to a directory containing FTDC files.                           |          n/a           |
| `start_time`       | FTDC time filter start.                                              | beginning of all files |
| `end_time`         | FTDC time filter end.                                                |    end of all files    |


```json
"BaselineAnalysisItem": {
  "chart_width": 450,
  "chart_height": 150
}
```

The fallback dimensions are defined in `ftdc_analysis/charts.py`.
Vertical grid lines are spaced every 100 pixels and horizontal grid lines every 50 pixels.
Workload and operation/latency charts use lines. Performance charts use bars.
Member-state charts are always 450×50 pixel bars.

#### 3.2.1 AI Analysis (Optional)
FTDC reports can include AI-generated summaries for each section (Workload,
Ops and Latencies, Performance). The analysis appears as a brief 2-3 sentence
assessment at the end of each section, flagging potential issues or confirming
normal operation.

**Configuration** — set the following environment variables:

| Variable          | Required | Default        | Description                             |
| ----------------- | :------: | -------------- | --------------------------------------- |
| `OPENAI_API_KEY`  |   Yes    | —              | API key for the AI service              |
| `OPENAI_BASE_URL` |    No    | OpenAI default | Compatible API endpoint (e.g. DeepSeek) |
| `AI_MODEL`        |    No    | `gpt-4o`       | Model name to use                       |

If `OPENAI_API_KEY` is not set, AI analysis is silently skipped.

**Example** `.env` file:
```bash
OPENAI_API_KEY="sk-..."
OPENAI_BASE_URL="https://api.deepseek.com"
AI_MODEL="deepseek-v4-pro"
```

Or export directly in the shell:
```bash
export OPENAI_API_KEY="sk-..."
x-ray ftdc /var/lib/mongo/diagnostic.data
```

