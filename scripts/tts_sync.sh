#!/bin/bash
# Sync Hypertext TTS export to Tabletop Simulator Saved Objects folder

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source and destination paths
TTS_EXPORT="$PROJECT_ROOT/series/2026-Q1/exports/tabletopsimulator"
TTS_SAVED_OBJECTS="/c/Users/mlmic/OneDrive/Documents/My Games/Tabletop Simulator/Saves/Saved Objects"

# Check if export exists
if [ ! -d "$TTS_EXPORT" ]; then
    echo "Error: TTS export not found at $TTS_EXPORT"
    echo "Run: python -m hypertext.lots.exporter --series series/2026-Q1 --target tabletopsimulator ..."
    exit 1
fi

# Check if TTS folder exists
if [ ! -d "$TTS_SAVED_OBJECTS" ]; then
    echo "Error: TTS Saved Objects folder not found at:"
    echo "  $TTS_SAVED_OBJECTS"
    echo ""
    echo "Update TTS_SAVED_OBJECTS in this script with your path."
    exit 1
fi

# Copy Hypertext.json
echo "Syncing Hypertext to TTS..."
cp "$TTS_EXPORT/Hypertext.json" "$TTS_SAVED_OBJECTS/"

if [ $? -eq 0 ]; then
    echo "Done! Hypertext.json copied to TTS Saved Objects."
    echo ""
    echo "In TTS: Objects > Saved Objects > Hypertext"
else
    echo "Error: Failed to copy Hypertext.json"
    exit 1
fi
