"""Main CLI entry point using argparse."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from otelfl.config import Settings
from otelfl.core.experiment_logger import ExperimentLogger
from otelfl.core.flagd_client import FlagdClient
from otelfl.core.locust_client import LocustClient
from otelfl.cli import flag_commands, load_commands, stats_commands, experiment_commands, scenario_commands


# Shared parent parser so --output-format works before or after the subcommand
_common_parser = argparse.ArgumentParser(add_help=False)
_common_parser.add_argument(
    "--output-format", "-f", choices=["text", "json"], default="text",
    help="Output format (default: text)",
)
_common_parser.add_argument("--flagd-config", help="Path to flagd config JSON file")
_common_parser.add_argument("--locust-url", help="Locust API base URL")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="otelfl",
        description="Control OpenTelemetry Demo feature flags and load generator",
        parents=[_common_parser],
    )

    subparsers = parser.add_subparsers(dest="command")
    flag_commands.register(subparsers, parents=[_common_parser])
    load_commands.register(subparsers, parents=[_common_parser])
    stats_commands.register(subparsers, parents=[_common_parser])
    experiment_commands.register(subparsers, parents=[_common_parser])
    scenario_commands.register(subparsers, parents=[_common_parser])
    subparsers.add_parser("tui", help="Launch interactive TUI", parents=[_common_parser])

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(2)

    settings = Settings()
    if args.flagd_config:
        from pathlib import Path
        settings.flagd_config = Path(args.flagd_config)
    if args.locust_url:
        settings.locust_url = args.locust_url

    output_json = args.output_format == "json"
    console = Console(no_color=output_json, soft_wrap=output_json)

    if args.command == "tui":
        from otelfl.tui.app import OtelFLApp
        app = OtelFLApp(settings=settings)
        app.run()
        return

    if args.command == "flag":
        client = FlagdClient(settings.flagd_config)
        code = flag_commands.run(args, client, console)
        sys.exit(code)

    if args.command in ("load", "stats"):
        client = LocustClient(base_url=settings.locust_url)
        try:
            if args.command == "load":
                code = load_commands.run(args, client, console)
            else:
                code = stats_commands.run(args, client, console)
        finally:
            client.close()
        sys.exit(code)

    if args.command == "scenario":
        client = FlagdClient(settings.flagd_config)
        code = scenario_commands.run(args, client, console)
        sys.exit(code)

    if args.command == "experiment":
        logger = ExperimentLogger()
        code = experiment_commands.run(args, logger, console)
        sys.exit(code)
