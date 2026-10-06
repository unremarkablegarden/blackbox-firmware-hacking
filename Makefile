# Blackbox RE/Modding Project — Top-Level Makefile
#
# Quick start:
#   make setup       — install all dependencies
#   make analyze     — analyze latest firmware
#   make strings     — extract all firmware strings
#   make disasm      — disassemble entry point
#   make compare     — diff v3.1.2 vs v3.1.9
#   make patch-test  — dry-run the example version patch
#   make build       — compile custom firmware

FIRMWARE_DIR = Firmwares
LATEST       = $(FIRMWARE_DIR)/blackbox-3.1.9.bin
PREV         = $(FIRMWARE_DIR)/BLACKBOX312.bin
TOOLS        = tools

.PHONY: setup analyze strings disasm disasm-vectors compare \
        patch-test patch-version ghidra-import build clean help \
        mod-001 mod-001-dry

# --- Setup ---
setup:
	chmod +x setup.sh ghidra/import.sh
	./setup.sh

# --- Analysis ---
analyze:
	python3 $(TOOLS)/analyze.py $(LATEST)

analyze-json:
	python3 $(TOOLS)/analyze.py $(LATEST) --json

analyze-all:
	@echo "=== v1.02 ===" && python3 $(TOOLS)/analyze.py $(FIRMWARE_DIR)/Blackbox102.BIN
	@echo ""
	@echo "=== v2.0E ===" && python3 $(TOOLS)/analyze.py $(FIRMWARE_DIR)/BLACKBOX20E.bin
	@echo ""
	@echo "=== v3.1.2 ===" && python3 $(TOOLS)/analyze.py $(PREV)
	@echo ""
	@echo "=== v3.1.9 ===" && python3 $(TOOLS)/analyze.py $(LATEST)

strings:
	python3 $(TOOLS)/extract_strings.py $(LATEST)

strings-raw:
	python3 $(TOOLS)/extract_strings.py $(LATEST) --raw

strings-ui:
	python3 $(TOOLS)/extract_strings.py $(LATEST) --category ui_label

strings-cpp:
	python3 $(TOOLS)/extract_strings.py $(LATEST) --category cpp_symbol

strings-errors:
	python3 $(TOOLS)/extract_strings.py $(LATEST) --category error

# --- Disassembly ---
disasm:
	python3 $(TOOLS)/disasm.py $(LATEST)

disasm-vectors:
	python3 $(TOOLS)/disasm.py $(LATEST) --vectors

disasm-addr:
	@echo "Usage: make disasm-at ADDR=0x08040400"
	@test -n "$(ADDR)" && python3 $(TOOLS)/disasm.py $(LATEST) --addr $(ADDR) --function || true

disasm-at:
	python3 $(TOOLS)/disasm.py $(LATEST) --addr $(ADDR) --function

# --- Comparison ---
compare:
	python3 $(TOOLS)/compare.py $(PREV) $(LATEST)

compare-all:
	python3 $(TOOLS)/compare.py $(FIRMWARE_DIR)/Blackbox102.BIN $(LATEST)

# --- Patching ---
patch-test:
	python3 $(TOOLS)/patch.py $(LATEST) --patch-file patches/examples/version_rename.json --dry-run

patch-version:
	@mkdir -p patched
	python3 $(TOOLS)/patch.py $(LATEST) -o patched/BLACKBOX.BIN --patch-file patches/examples/version_rename.json
	@echo "Patched firmware: patched/BLACKBOX.BIN"

# --- Mods ---
# Mod 001: DaisyBox Amber Blackout
#   Edit the theme:  mods/001-custom-branding/themes/theme-amber-blackout-v2.json
#   Then run:        make mod-001
MOD_001_DIR   = mods/001-custom-branding
MOD_001_THEME = $(MOD_001_DIR)/themes/theme-amber-blackout-v2.json
MOD_001_PATCH = $(MOD_001_DIR)/patch.json
MOD_001_OUT   = $(MOD_001_DIR)/output/BLACKBOX.BIN

mod-001: $(MOD_001_OUT)

$(MOD_001_PATCH): $(MOD_001_THEME) $(LATEST)
	python3 $(TOOLS)/theme2patch.py $< --firmware $(LATEST) --name DaisyBox --credit community --version 0.0.2 -o $@

$(MOD_001_OUT): $(MOD_001_PATCH) $(LATEST)
	@mkdir -p $(MOD_001_DIR)/output
	python3 $(TOOLS)/patch.py $(LATEST) -o $@ --patch-file $(MOD_001_PATCH)

mod-001-dry: $(MOD_001_PATCH)
	python3 $(TOOLS)/patch.py $(LATEST) --patch-file $(MOD_001_PATCH) --dry-run

# --- Ghidra ---
ghidra-import:
	./ghidra/import.sh $(LATEST)

# --- Custom firmware build ---
build:
	$(MAKE) -C custom

build-clean:
	$(MAKE) -C custom clean

# --- Utilities ---
hexdump:
	xxd -l 512 $(LATEST) | head -32

clean:
	rm -rf patched/
	$(MAKE) -C custom clean 2>/dev/null || true

help:
	@echo "Blackbox RE/Modding Project"
	@echo ""
	@echo "Setup:"
	@echo "  make setup            Install dependencies (brew, pip, ghidra)"
	@echo ""
	@echo "Analysis:"
	@echo "  make analyze          Analyze latest firmware (v3.1.9)"
	@echo "  make analyze-all      Analyze all firmware versions"
	@echo "  make analyze-json     Output analysis as JSON"
	@echo "  make strings          Extract & categorize all strings"
	@echo "  make strings-raw      Raw string dump (offset + string)"
	@echo "  make strings-ui       UI labels only"
	@echo "  make strings-cpp      C++ symbols only"
	@echo ""
	@echo "Disassembly:"
	@echo "  make disasm           Disassemble reset handler"
	@echo "  make disasm-vectors   Disassemble all interrupt handlers"
	@echo "  make disasm-at ADDR=0x...  Disassemble function at address"
	@echo ""
	@echo "Comparison:"
	@echo "  make compare          Compare v3.1.2 vs v3.1.9"
	@echo "  make compare-all      Compare v1.02 vs v3.1.9"
	@echo ""
	@echo "Patching:"
	@echo "  make patch-test       Dry-run example patch"
	@echo "  make patch-version    Apply version string patch"
	@echo ""
	@echo "Mods:"
	@echo "  make mod-001          Build mod 001 (theme -> patch -> firmware)"
	@echo "  make mod-001-dry      Dry-run mod 001"
	@echo "  (edit theme-amber-blackout.json, then 'make mod-001' rebuilds automatically)"
	@echo ""
	@echo "Ghidra:"
	@echo "  make ghidra-import    Import into Ghidra (headless)"
	@echo ""
	@echo "Custom Firmware:"
	@echo "  make build            Compile custom firmware"
	@echo "  make build-clean      Clean build artifacts"
