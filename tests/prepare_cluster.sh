#!/bin/bash
#
# Start a MongoDB cluster with mlaunch. The first argument is the path to the
# mongod binary; the second selects the topology:
#   rs - a 3-node replica set
#   sh - a sharded cluster (1 shard, 1 config server, 1 mongos)

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <mongod-path> <rs|sh>" >&2
    exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# mlaunch --binarypath expects the directory containing mongod, so accept
# either that directory or the full path to the mongod binary itself.
if [[ -d "$1" ]]; then
    binarypath="$1"
else
    binarypath="$(dirname "$1")"
fi

case "$2" in
    rs)
        topology=(--replicaset --nodes 3)
        ;;
    sh)
        topology=(--replicaset --sharded 1 --config 1 --mongos 1)
        ;;
    *)
        echo "Unknown cluster type: $2 (expected 'rs' or 'sh')" >&2
        exit 1
        ;;
esac

mkdir -p .tests/mongo && cd .tests/mongo
mlaunch init "${topology[@]}" --binarypath "$binarypath" --port 47017
# Wait for the cluster to be writable (the primary for a replica set, the
# mongos for a sharded cluster) before continuing.
ready=0
for _ in {1..120}; do
    if mongosh --quiet mongodb://localhost:47017 --eval 'quit(db.hello().isWritablePrimary ? 0 : 1)' >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
[ "$ready" -eq 1 ] || { echo "Timed out waiting for the cluster to become ready" >&2; exit 1; }

# Run every init script in misc/init-js/ (in sorted order) to seed the cluster.
init_scripts=("$ROOT"/misc/init-js/*.js)
if [ ! -f "${init_scripts[0]}" ]; then
    echo "No init scripts found in $ROOT/misc/init-js/" >&2
    exit 1
fi
for script in "${init_scripts[@]}"; do
    echo "Running init script: $(basename "$script")"
    mongosh --quiet mongodb://localhost:47017 "$script"
done
