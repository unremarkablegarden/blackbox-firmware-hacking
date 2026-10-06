#!/usr/bin/env python3
"""
Generate a patch.json from a theme JSON file and branding config.

Palette and version-string offsets are read from the target firmware, so one
theme builds against any version that contains the stock palette (3.1.2, 3.1.9).

Usage:
    python3 tools/theme2patch.py THEME.json --firmware Firmwares/blackbox-3.1.9.bin
    python3 tools/theme2patch.py THEME.json --firmware Firmwares/blackbox-3.1.9.bin --name "DaisyBox" --credit "community" --version "0.0.1"
"""

import re
import sys
import json
import argparse
from pathlib import Path

STOCK_PALETTE = [
    '#56565A', '#141414', '#FCFCFC', '#FF6AF3', '#09D7F5', '#FF0000', '#09D7F5', '#141414',
    '#666666', '#09D7F5', '#22BB22', '#BB2222', '#141414', '#000000', '#FFFFFF', '#444444',
    '#707070', '#22BB22', '#BB2222', '#FFFF00', '#BB2222', '#AAAAAA', '#00FFCC', '#BA00FF',
    '#2B2B2B', '#046B7A', '#09D7F5', '#777100', '#09D7F5', '#FFFFFF', '#09D7F5', '#FF6AF3',
    '#FFFFFF',
]


def rgb_to_bgra_hex(hex_color):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'{b:02X}{g:02X}{r:02X}FF'


def find_unique(data, pattern, what):
    """Return the only match of a regex, or exit."""
    matches = list(re.finditer(pattern, data))
    if len(matches) != 1:
        sys.exit(f"  ERROR: expected 1 {what} in firmware, found {len(matches)}")
    return matches[0]


def locate(firmware_path):
    """Find the palette offset and stock version string in a firmware image."""
    data = Path(firmware_path).read_bytes()
    stock = bytes.fromhex(''.join(rgb_to_bgra_hex(c) for c in STOCK_PALETTE))
    palette_base = find_unique(data, re.escape(stock), 'stock palette').start()
    # Version is the only bare "d.d.d" string; the splash reads it next to "blackbox" and "by 1010music".
    stock_version = find_unique(data, rb'(?<=\x00)\d\.\d\.\d(?=\x00)', 'version string').group().decode()
    return palette_base, stock_version


def generate_patch(theme_path, firmware_path, name='DaisyBox', credit='community', version='0.0.1'):
    theme = json.loads(Path(theme_path).read_text())
    palette_base, stock_version = locate(firmware_path)

    operations = []

    # Branding (only if different from stock)
    if name != 'blackbox':
        if len(name) > 8:
            print(f"  WARNING: name '{name}' is {len(name)} chars, max 8. Truncating.")
            name = name[:8]
        operations.append({
            'type': 'string_replace', 'old': 'blackbox', 'new': name,
            'comment': 'Boot splash product name',
        })

    if credit != 'by 1010music':
        pad = max(0, 12 - len(credit))
        operations.append({
            'type': 'string_replace', 'old': 'by 1010music', 'new': credit + ' ' * pad,
            'comment': 'Boot splash attribution',
        })

    if version != stock_version:
        if len(version) > 5:
            print(f"  WARNING: version '{version}' is {len(version)} chars, max 5. Truncating.")
            version = version[:5]
        operations.append({
            'type': 'string_replace', 'old': stock_version, 'new': version,
            'comment': 'Version string',
        })

    # Colors
    for idx_str, entry in sorted(theme['palette'].items(), key=lambda x: int(x[0])):
        idx = int(idx_str)
        new_color = entry['color']
        role = entry['role']

        if new_color.upper() == STOCK_PALETTE[idx].upper():
            continue

        offset = palette_base + idx * 4
        operations.append({
            'type': 'hex_patch',
            'offset': f'0x{offset:06X}',
            'expect': rgb_to_bgra_hex(STOCK_PALETTE[idx]),
            'bytes': rgb_to_bgra_hex(new_color),
            'comment': f'Palette[{idx}] {role}: {STOCK_PALETTE[idx]} -> {new_color}',
        })

    patch = {
        'name': f'{name} {theme["name"]}',
        'description': theme.get('description', ''),
        'author': theme.get('author', 'unknown'),
        'target_version': stock_version,
        'target_file': Path(firmware_path).name,
        'theme_file': Path(theme_path).name,
        'operations': operations,
    }

    return patch


def main():
    parser = argparse.ArgumentParser(description='Generate patch.json from a theme file')
    parser.add_argument('theme', help='Theme JSON file')
    parser.add_argument('--firmware', required=True, help='Stock firmware .bin the patch targets')
    parser.add_argument('--name', default='DaisyBox', help='Product name (max 8 chars)')
    parser.add_argument('--credit', default='community', help='Attribution line (max 12 chars)')
    parser.add_argument('--version', default='0.0.1', help='Version string (max 5 chars)')
    parser.add_argument('-o', '--output', help='Output patch.json path (default: same dir as theme)')
    args = parser.parse_args()

    patch = generate_patch(args.theme, args.firmware, args.name, args.credit, args.version)

    if args.output:
        out_path = args.output
    else:
        out_path = str(Path(args.theme).parent / 'patch.json')

    Path(out_path).write_text(json.dumps(patch, indent=2) + '\n')
    print(f"  Generated {out_path} ({len(patch['operations'])} operations)")


if __name__ == '__main__':
    main()
