#!/usr/bin/env python3
"""
Blackbox Firmware Patcher
Apply binary patches to firmware files. Supports hex patches, string replacement,
color palette changes, and patch files.

Usage:
    # Replace a string (same length or shorter, padded with nulls)
    python3 tools/patch.py Firmwares/BLACKBOX312.bin -o patched.bin --replace-string "by 1010music" "by euklides  "

    # Patch bytes at a file offset
    python3 tools/patch.py Firmwares/BLACKBOX312.bin -o patched.bin --hex-patch 0x8CED4:332E312E32 --hex-patch 0x8CED4:342E302E30

    # NOP out instructions at an address (address, not file offset)
    python3 tools/patch.py Firmwares/BLACKBOX312.bin -o patched.bin --nop 0x08040500 --nop 0x08040502

    # Apply a patch file
    python3 tools/patch.py Firmwares/BLACKBOX312.bin -o patched.bin --patch-file patches/my_patch.json

    # Dry run — show what would change
    python3 tools/patch.py Firmwares/BLACKBOX312.bin --replace-string "3.1.2" "3.1.X" --dry-run
"""

import struct
import sys
import argparse
import json
import shutil
from pathlib import Path

APP_BASE = 0x08040000
THUMB_NOP = b'\xBF\x00'  # 2-byte Thumb NOP


def addr_to_offset(addr):
    """Convert absolute address to file offset."""
    return addr - APP_BASE


def offset_to_addr(offset):
    """Convert file offset to absolute address."""
    return offset + APP_BASE


def find_all(data, needle):
    """Find all occurrences of a byte pattern in data."""
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
    """Replace a string in the firmware. New string must be <= old string length."""
    old_bytes = old_str.encode('ascii')
    new_bytes = new_str.encode('ascii')

    if len(new_bytes) > len(old_bytes):
        print(f"  ERROR: New string ({len(new_bytes)} bytes) longer than old ({len(old_bytes)} bytes)")
        print(f"  Pad the new string or use a shorter one.")
        return data, False

    # Pad with nulls
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
    """Patch raw bytes at a file offset."""
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


def apply_nop(data, address, dry_run=False):
    """NOP out a 2-byte Thumb instruction at the given address."""
    offset = addr_to_offset(address)
    if offset < 0 or offset >= len(data):
        print(f"  ERROR: Address 0x{address:08X} is outside firmware range")
        return data, False

    old_bytes = data[offset:offset + 2]
    print(f"  {'[DRY RUN] ' if dry_run else ''}NOP at addr 0x{address:08X} (offset 0x{offset:06X}):")
    print(f"    Old: {old_bytes.hex().upper()}")
    print(f"    New: {THUMB_NOP.hex().upper()} (NOP)")

    if not dry_run:
        data = bytearray(data)
        data[offset:offset + 2] = THUMB_NOP
        data = bytes(data)

    return data, True


def apply_patch_file(data, patch_path, dry_run=False):
    """Apply patches from a JSON patch file."""
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
        elif op_type == 'nop':
            data, ok = apply_nop(data, int(op['address'], 0), dry_run)
        else:
            print(f"  WARNING: Unknown operation type '{op_type}'")
            ok = False
        success = success and ok

    return data, success


def main():
    parser = argparse.ArgumentParser(description='Blackbox Firmware Patcher')
    parser.add_argument('firmware', help='Input firmware .bin file')
    parser.add_argument('-o', '--output', help='Output patched .bin file')
    parser.add_argument('--replace-string', nargs=2, action='append', default=[],
                        metavar=('OLD', 'NEW'), help='Replace ASCII string (can repeat)')
    parser.add_argument('--hex-patch', action='append', default=[],
                        metavar='OFFSET:HEXBYTES', help='Patch bytes at offset (e.g. 0x100:DEADBEEF)')
    parser.add_argument('--nop', type=lambda x: int(x, 0), action='append', default=[],
                        metavar='ADDR', help='NOP instruction at address (e.g. 0x08040500)')
    parser.add_argument('--patch-file', action='append', default=[],
                        metavar='FILE.json', help='Apply patches from JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    parser.add_argument('--base', type=lambda x: int(x, 0), default=APP_BASE,
                        help=f'Base address (default: 0x{APP_BASE:08X})')
    args = parser.parse_args()

    if not args.dry_run and not args.output:
        print("Error: --output required (or use --dry-run)")
        sys.exit(1)

    data = Path(args.firmware).read_bytes()
    print(f"  Loaded {len(data):,} bytes from {args.firmware}")
    print()

    any_patch = False

    for old, new in args.replace_string:
        data, ok = apply_string_replace(data, old, new, args.dry_run)
        any_patch = any_patch or ok
        print()

    for hp in args.hex_patch:
        offset, hex_bytes = hp.split(':', 1)
        data, ok = apply_hex_patch(data, offset, hex_bytes, args.dry_run)
        any_patch = any_patch or ok
        print()

    for addr in args.nop:
        data, ok = apply_nop(data, addr, args.dry_run)
        any_patch = any_patch or ok
        print()

    for pf in args.patch_file:
        data, ok = apply_patch_file(data, pf, args.dry_run)
        any_patch = any_patch or ok
        print()

    if not any_patch:
        print("  No patches applied.")
        sys.exit(1)

    if not args.dry_run:
        Path(args.output).write_bytes(data)
        print(f"  Written {len(data):,} bytes to {args.output}")
    else:
        print("  [DRY RUN] No files written.")


if __name__ == '__main__':
    main()
