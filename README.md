# otel_flagd

CLI/TUI tool to control [OpenTelemetry Demo](https://opentelemetry.io/docs/demo/) feature flags (via flagd JSON config files) and Locust load generation.

## Quick Start

Requires Python 3.12+. Tested with [uv](https://docs.astral.sh/uv/).

```bash
uv venv p312 --python 3.12 --seed
source p312/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Run directly (no install needed)
python otel_flagd

# Run with subcommands
python otel_flagd flag list
python otel_flagd load status
python otel_flagd scenario list
python otel_flagd tui
```

Or install as a package for the `otelfl` command:

```bash
pip install -e .
otelfl --help
```

## Configuration

Settings can be overridden with environment variables:

| Env Var | Default | Purpose |
|---------|---------|---------|
| `OTELFL_FLAGD_CONFIG` | `~/sideProjects/opentelemetry-demo/src/flagd/demo.flagd.json` | Path to flagd config JSON |
| `OTELFL_LOCUST_URL` | `http://10.0.0.5:8080/loadgen/` | Locust API base URL |
| `OTELFL_POLL_INTERVAL` | `2.0` | Poll interval in seconds |

## Architecture

```
CLI (otelfl/cli/)  ──┐
                     ├──▶  Core Services (otelfl/core/)
TUI (otelfl/tui/)  ──┘
```

- **Core services** — flagd file client, Locust HTTP client, experiment logger, run modes, chaos scenarios
- **CLI** — argparse subcommands: `flag`, `load`, `stats`, `experiment`, `scenario`, `tui`
- **TUI** — Textual app with 2x2 grid: Flag Panel, Load Panel, Stats Panel, Timeline Panel
