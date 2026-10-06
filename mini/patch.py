#!/usr/bin/env python3
"""
Apply a JSON patch file to a Blackbox firmware .bin.

Supports two operation types:
  - string_replace: pad-with-nulls ASCII string substitution (boot-splash branding)
  - hex_patch: raw bytes at a file offset (palette colours)

Usage:
    python3 patch.py BLACKBOX312.bin -o output/BLACKBOX.BIN --patch-file output/patch.json
    python3 patch.py BLACKBOX312.bin --patch-file output/patch.json --dry-run
"""

import sys
import argparse
import json
from pathlib import Path

APP_BASE = 0x08040000


def offset_to_addr(offset):
    return offset + APP_BASE


def find_all(data, needle):
    results = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx == -1:
            break
        results.append(idx)
        start = idx + 1
    return results


def apply_string_replace(data, old_str, new_str, dry_run=False):
    old_bytes = old_str.encode('ascii')
    new_bytes = new_str.encode('ascii')

    if len(new_bytes) > len(old_bytes):
        print(f"  ERROR: New string ({len(new_bytes)} bytes) longer than old ({len(old_bytes)} bytes)")
        return data, False

    new_bytes = new_bytes + b'\x00' * (len(old_bytes) - len(new_bytes))

    locations = find_all(data, old_bytes)
    if not locations:
        print(f"  WARNING: String '{old_str}' not found in firmware")
        return data, False

    for loc in locations:
        addr = offset_to_addr(loc)
        print(f"  {'[DRY RUN] ' if dry_run else ''}String patch at offset 0x{loc:06X} (addr 0x{addr:08X}):")
        print(f"    Old: {old_str!r}")
        print(f"    New: {new_str!r}")

    if not dry_run:
        data = bytearray(data)
        for loc in locations:
            data[loc:loc + len(old_bytes)] = new_bytes
        data = bytes(data)

    return data, True


def apply_hex_patch(data, offset_hex, hex_bytes, dry_run=False, expect=None):
    offset = int(offset_hex, 0) if isinstance(offset_hex, str) else offset_hex
    patch_bytes = bytes.fromhex(hex_bytes) if isinstance(hex_bytes, str) else hex_bytes
    addr = offset_to_addr(offset)

    if offset < 0 or offset + len(patch_bytes) > len(data):
        print(f"  ERROR: Offset 0x{offset:06X} is outside the firmware ({len(data):,} bytes)")
        return data, False

    old_bytes = data[offset:offset + len(patch_bytes)]
    # A mismatch means the patch was built for another firmware version.
    if expect is not None and old_bytes != bytes.fromhex(expect):
        print(f"  ERROR: Offset 0x{offset:06X} holds {old_bytes.hex().upper()}, expected {expect.upper()}")
        print(f"  Wrong firmware for this patch. Regenerate it with theme2patch.py.")
        return data, False

    print(f"  {'[DRY RUN] ' if dry_run else ''}Hex patch at offset 0x{offset:06X} (addr 0x{addr:08X}):")
    print(f"    Old: {old_bytes.hex().upper()}")
    print(f"    New: {patch_bytes.hex().upper()}")

    if not dry_run:
        data = bytearray(data)
        data[offset:offset + len(patch_bytes)] = patch_bytes
        data = bytes(data)

    return data, True


def apply_patch_file(data, patch_path, dry_run=False):
    with open(patch_path) as f:
        patch = json.load(f)

    print(f"  Patch: {patch.get('name', 'unnamed')}")
    print(f"  Description: {patch.get('description', 'none')}")
    print(f"  Author: {patch.get('author', 'unknown')}")
    print()

    success = True
    for op in patch.get('operations', []):
        op_type = op['type']
        if op_type == 'string_replace':
            data, ok = apply_string_replace(data, op['old'], op['new'], dry_run)
        elif op_type == 'hex_patch':
            data, ok = apply_hex_patch(data, op['offset'], op['bytes'], dry_run, op.get('expect'))
        else:
            print(f"  WARNING: Unknown operation type '{op_type}'")
            ok = False
        success = success and ok

    return data, success


def main():
    parser = argparse.ArgumentParser(description='Apply a JSON patch file to a Blackbox firmware .bin')
    parser.add_argument('firmware', help='Input firmware .bin file')
    parser.add_argument('-o', '--output', help='Output patched .bin file')
    parser.add_argument('--patch-file', required=True, metavar='FILE.json',
                        help='Patch JSON file (produced by theme2patch.py)')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    args = parser.parse_args()

    if not args.dry_run and not args.output:
        print("Error: --output required (or use --dry-run)")
        sys.exit(1)

    data = Path(args.firmware).read_bytes()
    print(f"  Loaded {len(data):,} bytes from {args.firmware}")
    print()

    data, ok = apply_patch_file(data, args.patch_file, args.dry_run)
    print()

    if not ok:
        print("  No patches applied.")
        sys.exit(1)

    if not args.dry_run:
        Path(args.output).write_bytes(data)
        print(f"  Written {len(data):,} bytes to {args.output}")
    else:
        print("  [DRY RUN] No files written.")


if __name__ == '__main__':
    main()
