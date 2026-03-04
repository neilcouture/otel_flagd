"""CLI fetch subcommand — fetch Prometheus metrics via otel_etl."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
from rich.console import Console

CHUNK_MINUTES = 5


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
    fetch_parser.add_argument(
        "--retries", type=int, default=3, help="Number of retries on failure (default: 3)"
    )
    fetch_parser.add_argument(
        "--chunk-minutes", type=int, default=CHUNK_MINUTES,
        help=f"Fetch in chunks of N minutes to avoid overloading Prometheus (default: {CHUNK_MINUTES})",
    )


def _discover_metrics(get_metrics_dataframe2, prometheus_url: str, max_retries: int):
    """Discover metrics with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            the_metrics_df = get_metrics_dataframe2(prometheus_url)
        except KeyError:
            if attempt < max_retries:
                time.sleep(10 * attempt)
                continue
            raise RuntimeError(
                "Prometheus returned no series data (possibly overloaded or unavailable)"
            )
        if the_metrics_df.empty or "metric" not in the_metrics_df.columns:
            if attempt < max_retries:
                time.sleep(10 * attempt)
                continue
            raise RuntimeError("No metrics found on Prometheus (empty response)")
        return the_metrics_df["metric"]
    raise RuntimeError("Failed to discover metrics")


def _fetch_chunk(client, metric_names, chunk_start, chunk_end, step, max_retries):
    """Fetch a single time chunk with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            return client.fetch_metrics_range(metric_names, chunk_start, chunk_end, step)
        except Exception:
            if attempt < max_retries:
                time.sleep(10 * attempt)
                continue
            raise


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
    max_retries = getattr(args, "retries", 3)
    chunk_minutes = getattr(args, "chunk_minutes", CHUNK_MINUTES)

    try:
        if not output_json:
            console.print(f"Discovering metrics on [cyan]{prometheus_url}[/] ...")
        the_metrics = _discover_metrics(get_metrics_dataframe2, prometheus_url, max_retries)

        if not output_json:
            console.print(f"Found [bold]{len(the_metrics)}[/] metric series")

        client = PrometheusClient(prometheus_url)

        # Build time chunks
        chunks = []
        chunk_start = start_time
        while chunk_start < end_time:
            chunk_end = min(chunk_start + timedelta(minutes=chunk_minutes), end_time)
            chunks.append((chunk_start, chunk_end))
            chunk_start = chunk_end

        all_dfs = []
        for i, (c_start, c_end) in enumerate(chunks, 1):
            if not output_json:
                mins = int((c_end - c_start).total_seconds() / 60)
                console.print(
                    f"  Chunk {i}/{len(chunks)}: fetching {mins} min "
                    f"({c_start.strftime('%H:%M')}–{c_end.strftime('%H:%M')}) ..."
                )
            chunk_df = _fetch_chunk(
                client, the_metrics, c_start, c_end, args.step, max_retries
            )
            all_dfs.append(chunk_df)

        raw_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
        raw_df.to_csv(args.outfile, index=False)

        if output_json:
            console.print(json.dumps({
                "file": args.outfile,
                "rows": len(raw_df),
                "metrics": len(the_metrics),
                "chunks": len(chunks),
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            }))
        else:
            console.print(
                f"[green]Saved [bold]{len(raw_df)}[/] rows to {args.outfile}[/]"
            )
        return 0
    except Exception as e:
        if output_json:
            console.print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/] {e}")
        return 1
