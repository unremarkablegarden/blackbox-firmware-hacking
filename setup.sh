#!/usr/bin/env bash
set -euo pipefail

# 1010music Blackbox RE/Dev Environment Setup
# Run: chmod +x setup.sh && ./setup.sh

echo "=== Blackbox Firmware Dev Environment Setup ==="
echo ""

# --- Homebrew packages ---
echo "[1/5] Installing ARM toolchain & analysis tools..."
brew install --quiet arm-none-eabi-gcc 2>/dev/null || brew upgrade arm-none-eabi-gcc 2>/dev/null || true
brew install --quiet binwalk 2>/dev/null || true
brew install --quiet qemu 2>/dev/null || true  # for optional emulation

# --- Python deps ---
echo "[2/5] Installing Python tools..."
pip3 install --quiet capstone pyelftools intelhex cmsis-svd

# --- Ghidra ---
echo "[3/5] Checking Ghidra..."
if [ -d "/Applications/ghidra" ] || [ -d "$HOME/ghidra" ] || command -v ghidraRun &>/dev/null || [ -n "${GHIDRA_HOME:-}" ]; then
    echo "  Ghidra found."
else
    echo "  Ghidra not found. Installing via Homebrew cask..."
    brew install --cask ghidra 2>/dev/null || {
        echo "  Could not install Ghidra via brew. Please install manually:"
        echo "  https://github.com/NationalSecurityAgency/ghidra/releases"
        echo "  Then set GHIDRA_HOME=/path/to/ghidra in your shell profile."
    }
fi

# --- STM32 SVD file (for Ghidra and peripheral register mapping) ---
echo "[4/5] Downloading STM32H7 SVD file..."
SVD_DIR="./tools/svd"
mkdir -p "$SVD_DIR"
if [ ! -f "$SVD_DIR/STM32H750x.svd" ]; then
    curl -sL "https://raw.githubusercontent.com/cmsis-svd/cmsis-svd-data/main/data/STMicro/STM32H750x.svd" \
        -o "$SVD_DIR/STM32H750x.svd" 2>/dev/null || echo "  SVD download failed — grab it manually from cmsis-svd GitHub repo"
fi
if [ ! -f "$SVD_DIR/STM32H743x.svd" ]; then
    curl -sL "https://raw.githubusercontent.com/cmsis-svd/cmsis-svd-data/main/data/STMicro/STM32H743x.svd" \
        -o "$SVD_DIR/STM32H743x.svd" 2>/dev/null || echo "  SVD download failed — grab it manually from cmsis-svd GitHub repo"
fi

# --- Verify ---
echo "[5/5] Verifying installation..."
echo ""
echo "  arm-none-eabi-gcc: $(command -v arm-none-eabi-gcc 2>/dev/null && arm-none-eabi-gcc --version | head -1 || echo 'NOT FOUND')"
echo "  arm-none-eabi-objdump: $(command -v arm-none-eabi-objdump 2>/dev/null || echo 'NOT FOUND')"
echo "  binwalk: $(command -v binwalk 2>/dev/null || echo 'NOT FOUND')"
echo "  python3: $(python3 --version 2>/dev/null || echo 'NOT FOUND')"
echo "  capstone (python): $(python3 -c 'import capstone; print(capstone.__version__)' 2>/dev/null || echo 'NOT FOUND')"
echo "  SVD files: $(ls tools/svd/*.svd 2>/dev/null | wc -l | tr -d ' ') found"
echo ""
echo "=== Setup complete ==="
echo ""
echo "Quick start:"
echo "  make analyze          # Analyze latest firmware"
echo "  make strings          # Extract all strings"
echo "  make disasm           # Disassemble vector table + entry point"
echo "  make ghidra-import    # Import into Ghidra (headless)"
echo "  make patch-colors     # Interactive color palette editor"
echo "  make build            # Build custom firmware (after setup)"
