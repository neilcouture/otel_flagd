#!/usr/bin/env bash
# Scenario: Normal → Spike → Normal
# Starts in normal mode, spikes to 20 users for 5 minutes, then returns to normal.

set -euo pipefail

echo "=== Starting normal mode ==="
otelfl load start --mode normal

echo "=== Waiting 5 seconds before spike ==="
sleep 5

echo "=== Spiking to 20 users for 5 minutes ==="
otelfl load start --mode high --run-time 5m

echo "=== Waiting 5 minutes for spike to complete ==="
sleep 300

echo "=== Returning to normal mode ==="
otelfl load start --mode normal

echo "=== Scenario complete ==="
