#!/bin/bash
set -e

if [ "$1" = 'server' ]; then
    # Check if library.json exists (matching start_server.sh behavior)
    if [ ! -f "library.json" ]; then
        echo "Library index not found. Building initial index..."
        python3 incremental_indexer.py
    fi
    echo "Starting Library Search Server..."
    echo "Access it at http://localhost:5000"
    exec python3 app.py

elif [ "$1" = 'index' ]; then
    shift
    echo "Starting Indexer..."
    exec python3 incremental_indexer.py "$@"

elif [ "$1" = 'full-index' ]; then
    echo "Starting Full Indexer (with Wikipedia expansion)..."
    exec python3 incremental_indexer.py --full

elif [ "$1" = 'dryrun' ]; then
    echo "Performing Indexing Dry Run..."
    exec python3 incremental_indexer.py --dry-run

elif [ "$1" = 'clean' ]; then
    echo "Cleaning metadata cache and library database..."
    rm -rf .metadata_cache library.json
    echo "Clean complete."

else
    # Fallback to executing the command as-is (allows 'rm', 'ls', etc.)
    exec "$@"
fi
