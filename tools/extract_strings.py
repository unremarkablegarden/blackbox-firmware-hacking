#!/usr/bin/env python3
"""
Extract and categorize strings from Blackbox firmware.
Outputs strings grouped by category: UI, C++ symbols, paths, RTOS, errors, etc.

Usage:
    python3 tools/extract_strings.py Firmwares/BLACKBOX312.bin
    python3 tools/extract_strings.py Firmwares/BLACKBOX312.bin --category ui
    python3 tools/extract_strings.py Firmwares/BLACKBOX312.bin --raw > strings.txt
"""

import re
import sys
import argparse
from pathlib import Path


def extract_strings(data, min_length=4):
    """Extract printable ASCII strings with offsets."""
    strings = []
    current = bytearray()
    start = 0
    for i, byte in enumerate(data):
        if 0x20 <= byte <= 0x7E:
            if not current:
                start = i
            current.append(byte)
        else:
            if len(current) >= min_length:
                strings.append((start, current.decode('ascii')))
            current = bytearray()
    if len(current) >= min_length:
        strings.append((start, current.decode('ascii')))
    return strings


def categorize(s):
    """Categorize a string."""
    if '::' in s:
        return 'cpp_symbol'
    if ':\\' in s or ('.cpp' in s and '/' in s) or ('.c' in s and '/' in s):
        return 'build_path'
    if s.endswith(':') and len(s) < 30:
        return 'ui_label'
    if any(s.startswith(p) for p in ('Error', 'Warning', 'Failed', 'Invalid', 'Cannot', 'Unable')):
        return 'error'
    if re.match(r'^\d+\.\d+\.[0-9A-Za-z]+$', s):
        return 'version'
    if s in ('defaultTask', 'audioTask', 'pcmStreamer', 'IDLE', 'Tmr Svc', 'USBH_Thread'):
        return 'rtos_task'
    if any(kw in s.lower() for kw in ['hal_', 'fatfs', 'usbh_', 'usbd_']):
        return 'hal_driver'
    if s.startswith('<') and s.endswith('>'):
        return 'xml'
    if any(kw in s for kw in ['Sample', 'Reverb', 'Delay', 'Filter', 'LFO', 'MIDI',
                               'Sequence', 'Granular', 'Slice', 'Pad', 'Track',
                               'Compressor', 'Distortion', 'Flanger', 'Chorus']):
        return 'audio_feature'
    if len(s) < 20 and s[0].isupper() and ' ' not in s:
        return 'ui_menu'
    return 'other'


CATEGORIES = {
    'cpp_symbol': 'C++ Symbols',
    'build_path': 'Build Paths',
    'ui_label': 'UI Labels',
    'ui_menu': 'UI Menu Items',
    'error': 'Error Messages',
    'version': 'Version Strings',
    'rtos_task': 'RTOS Tasks',
    'hal_driver': 'HAL/Driver',
    'xml': 'XML/Markup',
    'audio_feature': 'Audio Features',
    'other': 'Other',
}


def main():
    parser = argparse.ArgumentParser(description='Extract and categorize firmware strings')
    parser.add_argument('firmware', help='Firmware .bin file')
    parser.add_argument('--min-length', type=int, default=4, help='Minimum string length')
    parser.add_argument('--category', '-c', choices=list(CATEGORIES.keys()),
                        help='Show only this category')
    parser.add_argument('--raw', action='store_true', help='Raw output (offset + string, no categories)')
    args = parser.parse_args()

    data = Path(args.firmware).read_bytes()
    strings = extract_strings(data, args.min_length)

    if args.raw:
        for offset, s in strings:
            print(f"0x{offset:06X}\t{s}")
        return

    # Group by category
    groups = {}
    for offset, s in strings:
        cat = categorize(s)
        if args.category and cat != args.category:
            continue
        groups.setdefault(cat, []).append((offset, s))

    for cat in CATEGORIES:
        if cat not in groups:
            continue
        items = groups[cat]
        print(f"\n{'='*60}")
        print(f"  {CATEGORIES[cat]} ({len(items)})")
        print(f"{'='*60}")
        for offset, s in items:
            print(f"  0x{offset:06X}  {s}")


if __name__ == '__main__':
    main()
