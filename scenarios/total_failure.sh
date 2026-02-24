#!/usr/bin/env bash
# Scenario: Total Failure
# Enables all flags, ramps to 40 users in 20 seconds, holds for 5 minutes,
# then resets all flags and returns to normal mode.

set -euo pipefail

echo "=== Saving flag snapshot ==="
SNAPSHOT=$(mktemp /tmp/otelfl_snapshot_XXXXXX.json)
otelfl flag snapshot "$SNAPSHOT"

echo "=== Enabling all flags ==="
for flag in $(otelfl flag list -f json | python3 -c "import sys,json; [print(f['name']) for f in json.load(sys.stdin)]"); do
    otelfl flag enable "$flag"
    echo "  Enabled: $flag"
done

echo "=== Ramping to 40 users (spawn rate: 2/s, ~20 seconds) ==="
otelfl load start -u 40 -r 2 --run-time 5m

echo "=== Holding for 5 minutes ==="
sleep 300

echo "=== Restoring flags from snapshot ==="
otelfl flag restore "$SNAPSHOT"
rm -f "$SNAPSHOT"

echo "=== Returning to normal mode ==="
otelfl load start --mode normal

echo "=== Scenario complete ==="
