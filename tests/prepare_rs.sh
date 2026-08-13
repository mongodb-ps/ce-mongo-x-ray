#!/bin/bash
#
# Start a 3-node replica set with mlaunch, using the mongod binary passed as $1.

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <mongod-path>" >&2
    exit 1
fi

# mlaunch --binarypath expects the directory containing mongod, so accept
# either that directory or the full path to the mongod binary itself.
if [[ -d "$1" ]]; then
    binarypath="$1"
else
    binarypath="$(dirname "$1")"
fi

mkdir -p .tests/mongo && cd .tests/mongo
mlaunch init --replicaset --nodes 3 --binarypath "$binarypath" --port 47017
# Wait for election to complete before returning
sleep 10
