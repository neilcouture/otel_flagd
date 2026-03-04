"""CLI fetch subcommand — fetch Prometheus metrics via otel_etl."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from rich.console import Console


def register(subparsers: argparse._SubParsersAction, parents: list | None = None) -> None:
    fetch_parser = subparsers.add_parser(
        "fetch", help="Fetch Prometheus metrics to CSV", parents=parents or []
    )
    fetch_parser.add_argument(
        "--url", required=True, help="Prometheus base URL (e.g. http://localhost:9090)"
    )
    fetch_parser.add_argument(
        "--outfile", required=True, help="Output CSV file path"
    )
    fetch_parser.add_argument(
        "--minutes", type=int, default=60, help="How many minutes of data to fetch (default: 60)"
    )
    fetch_parser.add_argument(
        "--step", default="60s", help="Query resolution step (default: 60s)"
    )


def run(args: argparse.Namespace, console: Console) -> int:
    output_json = getattr(args, "output_format", "text") == "json"

    try:
        from otel_etl.utils import PrometheusClient, get_metrics_dataframe2
    except ImportError as e:
        msg = f"otel_etl is not importable: {e}"
        if output_json:
            console.print(json.dumps({"error": msg}))
        else:
            console.print(f"[red]Error:[/] {msg}")
        return 1

    prometheus_url = args.url
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=args.minutes)

    try:
        if not output_json:
            console.print(f"Discovering metrics on [cyan]{prometheus_url}[/] ...")
        the_metrics_df = get_metrics_dataframe2(prometheus_url)
        the_metrics = the_metrics_df['metric']

        if not output_json:
            console.print(f"Found [bold]{len(the_metrics)}[/] metric series")
            console.print(
                f"Fetching last [bold]{args.minutes}[/] minutes "
                f"(step={args.step}) ..."
            )
        client = PrometheusClient(prometheus_url)
        raw_df = client.fetch_metrics_range(the_metrics, start_time, end_time, args.step)

        raw_df.to_csv(args.outfile, index=False)

        if output_json:
            console.print(json.dumps({
                "file": args.outfile,
                "rows": len(raw_df),
                "metrics": len(the_metrics),
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            }))
        else:
            console.print(
                f"[green]Saved [bold]{len(raw_df)}[/] rows to {args.outfile}[/]"
            )
    except Exception as e:
        if output_json:
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/] {e}")
        return 1

    return 0
