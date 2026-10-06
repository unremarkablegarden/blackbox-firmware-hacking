#!/usr/bin/env python3
"""
Blackbox Firmware Comparator
Compare two firmware versions: size, strings, vector tables, and binary diffs.

Usage:
    python3 tools/compare.py Firmwares/BLACKBOX20E.bin Firmwares/BLACKBOX312.bin
"""

import struct
import sys
import argparse
from pathlib import Path

APP_BASE = 0x08040000


def extract_strings(data, min_length=8):
    """Extract printable ASCII strings."""
    strings = set()
    current = bytearray()
    for byte in data:
        if 0x20 <= byte <= 0x7E:
            current.append(byte)
        else:
            if len(current) >= min_length:
                strings.add(current.decode('ascii'))
            current = bytearray()
    if len(current) >= min_length:
        strings.add(current.decode('ascii'))
    return strings


def compare_vectors(data_a, data_b, name_a, name_b):
    """Compare vector tables."""
    count = 160
    diffs = []
    for i in range(count):
        va = struct.unpack_from('<I', data_a, i * 4)[0] if i * 4 + 4 <= len(data_a) else 0
        vb = struct.unpack_from('<I', data_b, i * 4)[0] if i * 4 + 4 <= len(data_b) else 0
        if va != vb:
            diffs.append((i, va, vb))
    return diffs


def binary_diff_regions(data_a, data_b, min_run=4):
    """Find contiguous regions that differ between two binaries."""
    min_len = min(len(data_a), len(data_b))
    regions = []
    i = 0
    while i < min_len:
        if data_a[i] != data_b[i]:
            start = i
            while i < min_len and data_a[i] != data_b[i]:
                i += 1
            if i - start >= min_run:
                regions.append((start, i - start))
        i += 1

    # Tail difference if sizes differ
    if len(data_a) != len(data_b):
        regions.append((min_len, abs(len(data_a) - len(data_b))))

    return regions


def main():
    parser = argparse.ArgumentParser(description='Blackbox Firmware Comparator')
    parser.add_argument('file_a', help='First firmware .bin')
    parser.add_argument('file_b', help='Second firmware .bin')
    parser.add_argument('--strings-only', action='store_true', help='Only compare strings')
    parser.add_argument('--max-diff-regions', type=int, default=20, help='Max diff regions to show')
    args = parser.parse_args()

    data_a = Path(args.file_a).read_bytes()
    data_b = Path(args.file_b).read_bytes()
    name_a = Path(args.file_a).name
    name_b = Path(args.file_b).name

    print(f"{'='*60}")
    print(f"  FIRMWARE COMPARISON")
    print(f"{'='*60}")
    print(f"  A: {name_a} ({len(data_a):,} bytes)")
    print(f"  B: {name_b} ({len(data_b):,} bytes)")
    delta = len(data_b) - len(data_a)
    pct = (delta / len(data_a)) * 100 if len(data_a) > 0 else 0
    print(f"  Delta: {delta:+,} bytes ({pct:+.1f}%)")
    print()

    # --- Strings comparison ---
    strings_a = extract_strings(data_a)
    strings_b = extract_strings(data_b)

    added = strings_b - strings_a
    removed = strings_a - strings_b
    common = strings_a & strings_b

    print(f"  STRINGS")
    print(f"    A: {len(strings_a):,}  |  B: {len(strings_b):,}")
    print(f"    Common: {len(common):,}  |  Added: {len(added):,}  |  Removed: {len(removed):,}")
    print()

    if added:
        print(f"  ADDED STRINGS ({len(added)}):")
        for s in sorted(added)[:50]:
            print(f"    + {s}")
        if len(added) > 50:
            print(f"    ... and {len(added) - 50} more")
        print()

    if removed:
        print(f"  REMOVED STRINGS ({len(removed)}):")
        for s in sorted(removed)[:50]:
            print(f"    - {s}")
        if len(removed) > 50:
            print(f"    ... and {len(removed) - 50} more")
        print()

    if args.strings_only:
        return

    # --- Vector table ---
    vdiffs = compare_vectors(data_a, data_b, name_a, name_b)
    print(f"  VECTOR TABLE CHANGES ({len(vdiffs)} differences):")
    for idx, va, vb in vdiffs[:20]:
        label = f"Vec[{idx}]"
        print(f"    {label:<10}  A: 0x{va:08X}  →  B: 0x{vb:08X}")
    print()

    # --- Binary diff ---
    regions = binary_diff_regions(data_a, data_b)
    print(f"  BINARY DIFF REGIONS ({len(regions)} regions >= 4 bytes):")
    total_diff_bytes = sum(size for _, size in regions)
    print(f"    Total differing bytes: {total_diff_bytes:,}")
    print()
    for offset, size in regions[:args.max_diff_regions]:
        addr = offset + APP_BASE
        print(f"    0x{offset:06X} (addr 0x{addr:08X}):  {size:,} bytes differ")
    if len(regions) > args.max_diff_regions:
        print(f"    ... and {len(regions) - args.max_diff_regions} more regions")
    print()


if __name__ == '__main__':
    main()
