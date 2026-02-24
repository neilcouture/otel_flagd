# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`otelfl` is a Python CLI/TUI tool for controlling OpenTelemetry Demo feature flags (via flagd JSON config files) and Locust load generation. It provides both a CLI with subcommands and an interactive Textual-based TUI dashboard.

## Commands

```bash
# Install (editable with dev deps)
pip install -e ".[dev]"

# Run CLI
otelfl --help
otelfl flag list
otelfl tui

# Tests
python -m pytest tests/                                          # all tests
python -m pytest tests/test_flagd_client.py                      # one module
python -m pytest tests/test_flagd_client.py::TestGetFlag::test_get_existing_flag  # single test

# Lint & format
ruff check src/otelfl
ruff format src/otelfl
```

## Architecture

Three interface layers share common core services:

```
CLI (otelfl/cli/)  ──┐
                     ├──▶  Core Services (otelfl/core/)
TUI (otelfl/tui/)  ──┘
```

**Core services** (`src/otelfl/core/`):
- `flagd_client.py` — Reads/writes flagd JSON config files directly on disk (no gRPC). Manages flag state, snapshots, and restore.
- `locust_client.py` — Sync (`LocustClient`) and async (`AsyncLocustClient`) HTTP clients for the Locust load generator API via httpx.
- `experiment_logger.py` — In-memory event tracking with JSON/CSV export for recording flag changes, load changes, and notes.
- `run_mode.py` — Manages named load levels (low/normal/high) with timed runs and auto-fallback.
- `scenarios.py` — Pre-configured chaos scenarios (7 presets) that apply specific flag states.

**CLI** (`src/otelfl/cli/`): argparse-based with subcommands: `flag`, `load`, `stats`, `experiment`, `scenario`, `tui`. Supports `--output-format {text,json}`.

**TUI** (`src/otelfl/tui/`): Textual app with a 2x2 grid layout — Flag Panel, Load Panel, Stats Panel, Timeline Panel. Styled via `styles.tcss`.

**Models** (`src/otelfl/models.py`): Dataclasses for `FlagDefinition`, `LocustStats`, `Experiment`, `ExperimentEvent`, `RunMode`, `Scenario`.

## Configuration

Settings are in `src/otelfl/config.py` as a `Settings` dataclass with env var overrides:

| Env Var | Default | Purpose |
|---------|---------|---------|
| `OTELFL_FLAGD_CONFIG` | `~/sideProjects/opentelemetry-demo/src/flagd/demo.flagd.json` | Path to flagd config JSON |
| `OTELFL_LOCUST_URL` | `http://10.0.0.5:8080/loadgen/` | Locust API base URL |
| `OTELFL_POLL_INTERVAL` | `2.0` | Poll interval in seconds |

## Key Conventions

- Python 3.11+, built with Hatchling
- Line length: 100 (ruff)
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- Source layout: `src/otelfl/` package with `tests/` at root
- FlagdClient works by direct JSON file manipulation, not gRPC — it reads/writes the flagd config file and relies on flagd's file watcher for hot-reload
