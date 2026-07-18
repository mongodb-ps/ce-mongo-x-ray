# x-ray
[![Makefile](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/makefile.yml)
[![Release](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml/badge.svg)](https://github.com/mongodb-ps/ce-mongo-x-ray/actions/workflows/release.yml)
[![PyPI](https://img.shields.io/pypi/v/mongo-x-ray.svg)](https://pypi.org/project/mongo-x-ray/)


This project aims to create tools for MongoDB analysis and diagnosis. So far 3 modules are being built:
- Health check module.
- Log analysis module.
- `getMongoData` visualization module (Under construction).

## 1 Compatibility Matrix
### 1.1 Health Check
|  Replica Set  | Sharded Cluster | Standalone |
| :-----------: | :-------------: | :--------: |
| >=4.2 &check; |  >=4.2 &check;  |  &cross;   |

Older versions are not tested.

### 1.2 Log Analysis
Log analysis requires JSON format logs, which is supported since 4.4.
|  Replica Set  | Sharded Cluster |  Standalone   |
| :-----------: | :-------------: | :-----------: |
| >=4.4 &check; |  >=4.4 &check;  | >=4.4 &check; |


### 1.3 getMongoData Analysis
Analyze & visualize the [getMongoData.js](https://github.com/mongodb/support-tools/tree/master/getMongoData) output.
|  Replica Set  | Sharded Cluster | Standalone |
| :-----------: | :-------------: | :--------: |
| >=4.4 &check; |  >=4.4 &check;  |  &cross;   |

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
cd x-ray
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
cd x-ray
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

## 3 Using the Tool
```bash
x-ray [-h] [-q] [-c CONFIG] {healthcheck,hc,log,gmd,ftdc}
```
| Argument         | Description                                                                                                                                                                                         |        Default         |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------: |
| `-q`, `--quiet`  | Quiet mode.                                                                                                                                                                                         |        `false`         |
| `-h`, `--help`   | Show the help message and exit.                                                                                                                                                                     |          n/a           |
| `-c`, `--config` | Path to configuration file.                                                                                                                                                                         | Built-in `config.json` |
| `command`        | Command to run. Include:<br/>- `healthcheck` or `hc`: Health check.<br/>- `log`: Log analysis.<br/>- `gmd`: getMongoData analysis.<br/>- `ftdc`: FTDC analysis.<br/>- `version`: Show version info. |          None          |

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
x-ray healthcheck [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] [uri]
```
| Argument           | Description                                                                       |  Default  |
| ------------------ | --------------------------------------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                                                  | `default` |
| `-o`, `--output`   | Output folder path.                                                               | `output/` |
| `-f`, `--format`   | Output format (`markdown`, `html`, or `pdf`). PDF also retains Markdown and HTML. |  `html`   |
| `uri`              | MongoDB database URI.                                                             |   None    |

For security reasons you may not want to include credentials in the command. There are 2 options:
- If the URI is not provided, user will be asked to input one.
- If URI is provided but not username/password, user will also be asked to input them.

#### 3.1.3 More Info
Refer to the wiki for more details.
- [Customize the thresholds](https://github.com/mongodb-ps/ce-mongo-x-ray/wiki/Health-Check-Configuration)
- [Database permissions](https://github.com/mongodb-ps/ce-mongo-x-ray/wiki/Health-Check-Database-Permissions)
- [Output](https://github.com/mongodb-ps/ce-mongo-x-ray/wiki/Health-Check-Output)
- [Customize the output](https://github.com/mongodb-ps/ce-mongo-x-ray/wiki/Health-Check-Output-Template)

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
x-ray log [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] [log_file]
```
| Argument           | Description                                                                       |  Default  |
| ------------------ | --------------------------------------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                                                  | `default` |
| `-o`, `--output`   | Output folder path.                                                               | `output/` |
| `-f`, `--format`   | Output format (`markdown`, `html`, or `pdf`). PDF also retains Markdown and HTML. |  `html`   |
| `-r`, `--rate`     | Sample rate. Only analyze a subset of logs.                                       |    `1`    |
| `--top`            | When analyzing the slow queries, only list top N.                                 |   `10`    |

### 3.3 getMongoData Analysis Component
#### 3.3.1 Examples
```bash
# getMongoData output for a sharded cluster
x-ray gmd misc/getMongoData-sh.json
# getMongoData output for a replica set
x-ray gmd misc/getMongoData-rs.json
```

#### 3.3.2 Full Arguments
```bash
x-ray gmd [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] gmd_file
```
| Argument           | Description                                                                       |  Default  |
| ------------------ | --------------------------------------------------------------------------------- | :-------: |
| `-s`, `--checkset` | Checkset to run.                                                                  | `default` |
| `-o`, `--output`   | Output folder path.                                                               | `output/` |
| `-f`, `--format`   | Output format (`markdown`, `html`, or `pdf`). PDF also retains Markdown and HTML. |  `html`   |

### 3.4 FTDC Analysis Component

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
```

```bash
x-ray ftdc [-h] [-s CHECKSET] [-o OUTPUT] [-f {markdown,html,pdf}] [-r RATE] ftdc_path [start_time] [end_time]
```
| Argument           | Description                                                          |        Default         |
| ------------------ | -------------------------------------------------------------------- | :--------------------: |
| `-s`, `--checkset` | Checkset to run.                                                     |       `default`        |
| `-o`, `--output`   | Output folder path.                                                  |       `output/`        |
| `-r`, `--rate`     | controls FTDC sampling and accepts a value between `0` and `1`.      |  `1 / ingested files`  |
| `-f`, `--format`   | Output format (`html` or `pdf`). PDF also retains Markdown and HTML. |         `html`         |
| `ftdc_path`        | Point to a folder of ftdc files or a single ftdc file                |          n/a           |
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

### 3.5 Table Column Widths

Markdown pipe tables support a `{width}` spec on header cells to set column widths
in generated HTML and PDF output:

```
| Name{120} | Description{*} | Status{50%} |
| --------- | -------------- | ----------- |
| foo       | bar            | active      |
```

| Spec      | Meaning                                    | Example HTML                    |
| --------- | ------------------------------------------ | ------------------------------- |
| `{N}`     | CSS width — bare numbers default to pixels | `<col style="width:120px" ...>` |
| `{Npx}`   | Explicit pixels                            | `<col style="width:120px" ...>` |
| `{N%}`    | Percentage of the table width              | `<col style="width:50%" ...>`   |
| `{Nunit}` | Any valid CSS unit (`em`, `rem`, `vw`, …)  | `<col style="width:10em">`      |
| `{*}`     | Auto (no constraint)                       | `<col />`                       |

The spec is stripped from the rendered header text and a `<colgroup>` of `<col>`
elements is inserted into the `<table>`. Columns without a `{width}` spec are
left unconstrained.
