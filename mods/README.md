# Blackbox Mods

Each mod lives in its own numbered folder with a patch file and documentation.

## Structure

```
mods/
├── 001-custom-branding/    First mod: splash text, version, color theme
│   ├── patch.json          The patch definition
│   ├── notes.md            What it does, why, and what we learned
│   └── output/             Built firmware goes here
├── 002-xxx/                Next mod...
└── README.md               This file
```

## Creating a new mod

```bash
# Create the directory
mkdir -p mods/002-my-mod/output

# Write a patch.json (see 001 for the format), or generate one from a theme
python3 tools/theme2patch.py mods/002-my-mod/theme.json --firmware Firmwares/blackbox-3.1.9.bin -o mods/002-my-mod/patch.json

# Test it (dry run)
python3 tools/patch.py Firmwares/blackbox-3.1.9.bin --patch-file mods/002-my-mod/patch.json --dry-run

# Build it
python3 tools/patch.py Firmwares/blackbox-3.1.9.bin -o mods/002-my-mod/output/BLACKBOX.BIN --patch-file mods/002-my-mod/patch.json
```

## Flashing

1. Copy `output/BLACKBOX.BIN` to the root of a FAT32 microSD card
2. Insert SD card into Blackbox
3. Power on while holding the encoder button (check manual for exact update procedure)
4. Wait ~15 seconds for the update to complete

## Reverting

Flash the stock firmware: copy `Firmwares/blackbox-3.1.9.bin` to the SD card as `BLACKBOX.BIN`.
