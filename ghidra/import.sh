#!/usr/bin/env bash
set -euo pipefail

# Import Blackbox firmware into Ghidra for headless analysis
# Usage: ./ghidra/import.sh [firmware.bin]
#
# Requires GHIDRA_HOME to be set, or Ghidra installed via brew

FIRMWARE="${1:-Firmwares/BLACKBOX312.bin}"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="BlackboxProject"
SCRIPT_DIR="$PROJECT_DIR/scripts"

# Find Ghidra
if [ -n "${GHIDRA_HOME:-}" ]; then
    GHIDRA="$GHIDRA_HOME"
elif [ -d "/Applications/ghidra" ]; then
    GHIDRA="/Applications/ghidra"
elif command -v ghidraRun &>/dev/null; then
    GHIDRA="$(dirname "$(command -v ghidraRun)")"
else
    # Check common homebrew locations
    GHIDRA_CASK="$(brew --prefix 2>/dev/null)/Caskroom/ghidra"
    if [ -d "$GHIDRA_CASK" ]; then
        GHIDRA="$(ls -d "$GHIDRA_CASK"/*/ghidra_* 2>/dev/null | tail -1)"
    fi
fi

if [ -z "${GHIDRA:-}" ] || [ ! -d "$GHIDRA" ]; then
    echo "Error: Ghidra not found. Set GHIDRA_HOME or install via: brew install --cask ghidra"
    exit 1
fi

ANALYZE_HEADLESS="$GHIDRA/support/analyzeHeadless"

if [ ! -f "$ANALYZE_HEADLESS" ]; then
    echo "Error: analyzeHeadless not found at $ANALYZE_HEADLESS"
    exit 1
fi

echo "=== Ghidra Headless Import ==="
echo "  Ghidra:    $GHIDRA"
echo "  Firmware:  $FIRMWARE"
echo "  Project:   $PROJECT_DIR/$PROJECT_NAME"
echo ""

# Import and run analysis + our labeling script
"$ANALYZE_HEADLESS" \
    "$PROJECT_DIR" "$PROJECT_NAME" \
    -import "$FIRMWARE" \
    -processor "ARM:LE:32:Cortex" \
    -loader BinaryLoader \
    -loader-baseAddr "0x08040000" \
    -postScript "$SCRIPT_DIR/BlackboxImport.py" \
    -overwrite \
    -analysisTimeoutPerFile 600

echo ""
echo "=== Import complete ==="
echo "Open in Ghidra GUI: File -> Open Project -> $PROJECT_DIR/$PROJECT_NAME.gpr"
