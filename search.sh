#!/bin/bash
# Zoek fotografiemateriaal — wrapper script
# Gebruik: ./search.sh "Nikkor 35mm f/2 AI lens"

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "Gebruik: ./search.sh \"beschrijving van wat je zoekt\""
    exit 1
fi

echo "J" | python3 main.py "$1"
