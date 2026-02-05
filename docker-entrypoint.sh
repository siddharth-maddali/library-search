#!/bin/bash
set -e

if [ "$1" = 'server' ]; then
    echo "Starting Library Search Server..."
    exec python3 app.py
elif [ "$1" = 'index' ]; then
    shift
    echo "Starting Indexer..."
    exec python3 incremental_indexer.py "$@"
else
    echo "Usage:"
    echo "  docker run <image> server          - Start the web server"
    echo "  docker run <image> index [--full] [--cores N] [--dry-run] - Run the indexer"
    exec "$@"
fi
