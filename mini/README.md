# mini — Blackbox colour mod

Minimal self-contained tree for re-skinning the 1010music Blackbox v3.1.9
firmware: palette swap plus optional boot-splash branding (product name,
attribution, version string).

## Usage

```
make dry      # preview the planned patches
make          # build output/BLACKBOX.BIN
make clean    # remove output/
```

Then copy `output/BLACKBOX.BIN` to the Blackbox SD card and update normally.

## Customising

Edit `theme.json`. Each entry under `palette` is a `{role, color, description}`
object keyed by index 0–32. Hex colours in `#RRGGBB` form. To revert a single
slot to stock, set its colour to the stock value (see `STOCK_PALETTE` in
`theme2patch.py`) and it will be omitted from the patch.

To change the boot splash, edit the `python3 theme2patch.py` line in the
`Makefile` and pass `--name`, `--credit`, `--version` (max 8 / 12 / 5 chars).

To build for another firmware version, put its `.bin` here and set `FIRMWARE` in the `Makefile`. Works for any version that contains the stock palette (3.1.2 and 3.1.9 do).

## Files

- `theme.json` — colour definitions (Monochrome theme by default)
- `theme2patch.py` — converts `theme.json` to a patch JSON; reads palette and version offsets from the firmware
- `patch.py` — applies a patch JSON to the firmware binary
- `blackbox-3.1.9.bin` — stock firmware (v3.1.9, not in git; download from 1010music)
- `Makefile` — drives the two-step build

Stdlib-only Python; no `pip` deps.

For the full reverse-engineering / modding toolkit (analysis, disassembly,
Ghidra, custom firmware), see the parent directory.
