# Blackbox firmware hacking

Reverse engineering, analysis and modding toolkit for the 1010music Blackbox sampler firmware.

The firmware has no CRC, signature or encryption, and the bootloader sits in a separate flash region that updates never touch. A patched `.bin` loads like an official update, and a bad patch is reverted by flashing the stock file again.

## Hardware

- **MCU:** STM32H750 (ARM Cortex-M7, up to 480 MHz)
- **RAM:** 64 MB external SDRAM, 1 MB on-chip SRAM
- **Firmware:** C++ on FreeRTOS, 728,696 bytes (v3.1.9)
- **Internal codename:** BoomboxFramework

Full detail: [hardware report](docs/1010music-blackbox-hardware-report.md).

## Layout

```
├── Firmwares/      Stock firmware: v1.02 (2019), v2.0E (2022), v3.1.2 (2024), v3.1.9 (2025, latest)
├── Manuals/        Official user manual (not in git)
├── tools/          Python analysis and patching scripts
├── patches/        Example patch files (JSON)
├── mods/           Numbered mods, each with patches, themes and notes
├── mini/           Self-contained colour mod: theme.json → BLACKBOX.BIN, stdlib Python only
├── ghidra/         Headless import script and analysis scripts
├── custom/         Bare-metal custom firmware (startup, linker script, Makefile)
├── docs/           Research reports
├── Makefile        Top-level commands
└── setup.sh        Dependency installer
```

### Tools

| Script | Purpose |
|--------|---------|
| `analyze.py` | Vector table, strings, protection checks |
| `disasm.py` | ARM Thumb-2 disassembly (capstone) |
| `extract_strings.py` | Categorised string extraction |
| `compare.py` | Diff between firmware versions |
| `patch.py` | Applies a JSON patch to a firmware binary |
| `theme2patch.py` | Converts a theme JSON to a patch JSON |

## Quick start

```bash
make setup           # install dependencies
make analyze         # analyse v3.1.9
make strings         # extract strings (also strings-ui, strings-cpp, strings-errors)
make disasm          # disassemble the entry point
make disasm-vectors  # disassemble the interrupt handlers
make compare         # diff v3.1.2 against v3.1.9
make patch-test      # dry-run the example version patch
make ghidra-import   # import v3.1.9 into Ghidra
make help            # all targets
```

## Colour themes

The UI palette is 33 ARGB32 entries. The boot splash shows three strings: product name, attribution and version. Their offsets differ between firmware versions, so `theme2patch.py` finds them in the firmware passed with `--firmware`. It searches for the stock palette and the only bare `d.d.d` version string, and stops if either does not match exactly once. Offsets per version and the stock palette are in [mods/001-custom-branding/notes.md](mods/001-custom-branding/notes.md).

The simplest route is `mini/`:

```bash
cd mini
# edit theme.json
make dry   # preview the patch
make       # writes output/BLACKBOX.BIN
```

See [mini/README.md](mini/README.md). Themes for mod 001 are in `mods/001-custom-branding/themes/`. `make mod-001` builds the Amber Blackout v2 theme.

A generated patch only fits the firmware it was generated from. To target another version, regenerate it:

```bash
python3 tools/theme2patch.py mods/001-custom-branding/themes/theme-monochrome.json \
  --firmware Firmwares/blackbox-3.1.9.bin --name DaisyBox --credit community --version 0.0.2 -o patch.json
```

## Patch format

```json
{
    "name": "My Patch",
    "description": "What it does",
    "operations": [
        {"type": "string_replace", "old": "3.1.2", "new": "3.1.X"},
        {"type": "nop", "address": "0x08040500"},
        {"type": "hex_patch", "offset": "0x1000", "expect": "00000000", "bytes": "DEADBEEF"}
    ]
}
```

```bash
python3 tools/patch.py Firmwares/blackbox-3.1.9.bin --patch-file my_patch.json --dry-run
python3 tools/patch.py Firmwares/blackbox-3.1.9.bin -o BLACKBOX.BIN --patch-file my_patch.json
```

`address` is a flash address. `offset` is a file offset. The file loads at `0x08040000`. `expect` is optional: the original bytes at `offset`. If they differ, `patch.py` writes nothing, so a patch applied to the wrong firmware version fails instead of corrupting it. `theme2patch.py` always sets it.

## Flashing and reverting

1. Copy the patched file to the root of a FAT32 microSD card as `BLACKBOX.BIN`.
2. Insert the card, hold the encoder and power on. Check the manual for the exact procedure.
3. Wait for the update to finish, about 15 s.

To revert, flash the stock file (`Firmwares/blackbox-3.1.9.bin`) the same way. If you have SWD access, dump the full flash, including the bootloader, before you modify anything.

## Memory map

```
Flash
  0x08000000–0x0803FFFF   Bootloader (256 KB, not in the .bin files)
  0x08040000–0x080E9000   Application (.bin loads here)

RAM
  0x20000000–0x2001FFFF   DTCM (128 KB)
  0x24000000–0x2407FFFF   AXI SRAM (512 KB, stack and heap)
  0x30000000–0x30047FFF   SRAM1–3 (288 KB, DMA buffers)
  External                64 MB SDRAM (sample cache)
```

## Custom firmware

```bash
brew install arm-none-eabi-gcc
make build                                               # → custom/build/
make -C custom flash-swd                                 # via SWD probe
make -C custom flash-sd SD_VOLUME=/Volumes/YOUR_SD_CARD  # via SD card
```

## Dependencies

- Python 3.10+ with `capstone`, `pyelftools`, `intelhex` (not needed for `mini/`)
- `arm-none-eabi-gcc` for custom firmware
- Ghidra for deep analysis
- Optional: `binwalk`

## Reports

- [Hardware deep dive](docs/1010music-blackbox-hardware-report.md)
- [Modding guide](docs/1010music-blackbox-modding-guide.md)
- [Precedents and prior art](docs/research-precedents-reverse-engineering.md)

## Repository notes

All `.bin` files are gitignored, both the stock firmware and patched output, as are `custom/build/` and `output/` directories. Download the stock firmware from 1010music and put it in `Firmwares/` (`blackbox-3.1.9.bin`, `BLACKBOX312.bin`, `BLACKBOX20E.bin`, `Blackbox102.BIN`) and in `mini/` (`blackbox-3.1.9.bin`). The user manual PDF is also gitignored; download it from 1010music into `Manuals/`.
