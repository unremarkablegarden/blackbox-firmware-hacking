# Mod 001: Custom Branding & Color Theme

## What it does

- **Boot splash**: "blackbox / by 1010music" → "BLCKBOX+ / community"
- **Version string**: "3.1.2" → "3.1.M" (M = modded)
- **UI accent color**: Cyan `#09D7F5` → Warm amber `#F5A623` (6 palette entries)
- **Dimmed accent**: Dark teal `#046B7A` → Dark amber `#07533D`

## Technical details

- **42 bytes changed** out of 695,920 (0.006% of firmware)
- Vector table and all code untouched
- File size identical to original
- Based on stock firmware v3.1.2 (Feb 2024)

## Color palette layout

The palette is 33 x ARGB32 values in little-endian (BGRA byte order), at file offset `0x0A9D7C` in v3.1.2 and `0x0B1D84` in v3.1.9. The 33 stock values are identical in both. `tools/theme2patch.py` finds the palette by searching for them.

Cyan accent appears at palette indices: 4, 6, 9, 26, 28, 30

| Index | Role (observed) | Stock | Modded |
|-------|----------------|-------|--------|
| 0 | Border/frame gray | `#56565A` | unchanged |
| 1 | Background dark | `#141414` | unchanged |
| 2 | Near-white text | `#FCFCFC` | unchanged |
| 3 | Pink/magenta accent | `#FF6AF3` | unchanged |
| **4** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 5 | Pure red (alert) | `#FF0000` | unchanged |
| **6** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 7 | Background dark | `#141414` | unchanged |
| 8 | Inactive gray | `#666666` | unchanged |
| **9** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 10 | Active green | `#22BB22` | unchanged |
| 11 | Alert red | `#BB2222` | unchanged |
| 12 | Background dark | `#141414` | unchanged |
| 13 | Pure black | `#000000` | unchanged |
| 14 | Pure white | `#FFFFFF` | unchanged |
| 15 | Border gray | `#444444` | unchanged |
| 16 | Mid gray | `#707070` | unchanged |
| 17 | Active green | `#22BB22` | unchanged |
| 18 | Alert red | `#BB2222` | unchanged |
| 19 | Yellow | `#FFFF00` | unchanged |
| 20 | Alert red | `#BB2222` | unchanged |
| 21 | Light gray | `#AAAAAA` | unchanged |
| 22 | Mint | `#00FFCC` | unchanged |
| 23 | Purple | `#BA00FF` | unchanged |
| 24 | Dark panel | `#2B2B2B` | unchanged |
| **25** | **Dimmed accent** | `#046B7A` | `#07533D` |
| **26** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 27 | Olive/dark yellow | `#777100` | unchanged |
| **28** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 29 | White text | `#FFFFFF` | unchanged |
| **30** | **Primary accent** | `#09D7F5` | `#F5A623` |
| 31 | Pink accent | `#FF6AF3` | unchanged |
| 32 | White text | `#FFFFFF` | unchanged |

## String locations

| String | v3.1.2 offset | v3.1.9 offset | Max length |
|--------|---------------|---------------|------------|
| Product name | `0x08CEC0` | `0x08FAA0` | 8 bytes (null-terminated, 12 byte slot) |
| Attribution | `0x08CECC` | `0x08FAAC` | 12 bytes (null-terminated, 16 byte slot) |
| Version | `0x08CEDC` | `0x08F290` | 5 bytes (null-terminated, 8 byte slot) |
| "Please insert" | `0x08CE1C` | `0x08F9FC` | 13 bytes |
| "microSD card" | `0x08CE2C` | `0x08FA0C` | 12 bytes |

In v3.1.9 the version string no longer sits next to the other splash strings. The splash code still loads all three from adjacent literal-pool words (`0x0872C0`–`0x0872C8` in v3.1.9, `0x02EC24`–`0x02EC2C` in v3.1.2), so the version shown on the splash is still that string.

## How to flash

1. Copy `output/BLACKBOX.BIN` to a FAT32 microSD card root
2. Insert into Blackbox
3. Hold the encoder down and power on
4. Wait for update (~15 sec)

## How to revert

Copy the stock firmware (`Firmwares/blackbox-3.1.9.bin`) to the SD card as `BLACKBOX.BIN` and re-flash.
