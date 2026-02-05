#!/bin/bash
# Check if library.json exists
if [ ! -f "library.json" ]; then
    echo "Building library index..."
    python3 incremental_indexer.py
fi

pkill -f "python3 app.py" || true
echo "Starting Library Search Server..."
echo "Access it at http://localhost:5000"
python3 app.py
