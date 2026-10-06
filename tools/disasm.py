#!/usr/bin/env python3
"""
Blackbox Firmware Disassembler
Uses the capstone engine to disassemble ARM Thumb-2 code from firmware binaries.

Usage:
    python3 tools/disasm.py Firmwares/BLACKBOX312.bin                    # Entry point
    python3 tools/disasm.py Firmwares/BLACKBOX312.bin --addr 0x08040400  # Specific address
    python3 tools/disasm.py Firmwares/BLACKBOX312.bin --addr 0x08040400 --count 50
    python3 tools/disasm.py Firmwares/BLACKBOX312.bin --vectors          # All vector handlers
"""

import struct
import sys
import argparse
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
except ImportError:
    print("Error: capstone not installed. Run: pip3 install capstone")
    sys.exit(1)

APP_BASE = 0x08040000


def _set_base(base):
    global APP_BASE
    APP_BASE = base


def disassemble(data, start_addr, count=30):
    """Disassemble Thumb-2 code starting at given address."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = True

    # Convert absolute address to file offset
    offset = start_addr - APP_BASE
    if offset < 0 or offset >= len(data):
        print(f"Error: address 0x{start_addr:08X} is outside firmware range")
        print(f"  Valid range: 0x{APP_BASE:08X} - 0x{APP_BASE + len(data):08X}")
        return

    chunk = data[offset:offset + count * 4]  # Rough estimate of bytes needed
    instructions = list(md.disasm(chunk, start_addr))

    for i, insn in enumerate(instructions[:count]):
        # Get raw bytes as hex
        raw = ' '.join(f'{b:02X}' for b in insn.bytes)
        print(f"  0x{insn.address:08X}:  {raw:<12}  {insn.mnemonic:<8} {insn.op_str}")


def disassemble_function(data, start_addr, max_insns=200):
    """Disassemble until we hit a return or branch-to-self."""
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    md.detail = True

    offset = start_addr - APP_BASE
    if offset < 0 or offset >= len(data):
        print(f"Error: address 0x{start_addr:08X} is outside firmware range")
        return

    chunk = data[offset:offset + max_insns * 4]
    count = 0
    for insn in md.disasm(chunk, start_addr):
        raw = ' '.join(f'{b:02X}' for b in insn.bytes)
        print(f"  0x{insn.address:08X}:  {raw:<12}  {insn.mnemonic:<8} {insn.op_str}")
        count += 1

        # Stop at function endings
        if insn.mnemonic in ('bx', 'pop') and 'pc' in insn.op_str:
            break
        if insn.mnemonic == 'b' and count > 1:
            # Unconditional branch might be tail call or loop — stop if backward
            try:
                target = int(insn.op_str.replace('#', ''), 16)
                if target <= insn.address:
                    break
            except ValueError:
                pass
        if count >= max_insns:
            print(f"  ... (stopped at {max_insns} instructions)")
            break


def show_vectors(data):
    """Disassemble the first few instructions of each active interrupt handler."""
    vectors = []
    for i in range(160):
        if i * 4 + 4 > len(data):
            break
        vectors.append(struct.unpack_from('<I', data, i * 4)[0])

    # Find default handler (most common)
    handler_counts = {}
    for v in vectors[16:]:
        if v != 0:
            handler_counts[v] = handler_counts.get(v, 0) + 1
    default_handler = max(handler_counts, key=handler_counts.get) if handler_counts else 0

    # Exception names
    exc_names = [
        "Initial_SP", "Reset", "NMI", "HardFault", "MemManage", "BusFault",
        "UsageFault", "Rsvd7", "Rsvd8", "Rsvd9", "Rsvd10", "SVCall",
        "DebugMon", "Rsvd13", "PendSV", "SysTick",
    ]

    print(f"  {'='*60}")
    print(f"  VECTOR TABLE DISASSEMBLY")
    print(f"  {'='*60}")
    print(f"  Default handler: 0x{default_handler:08X}")
    print()

    # Show reset handler
    print(f"  --- Reset Handler (0x{vectors[1]:08X}) ---")
    disassemble(data, vectors[1] & 0xFFFFFFFE, count=20)
    print()

    # Show unique non-default handlers
    seen = set()
    for i in range(2, min(len(vectors), 160)):
        v = vectors[i]
        if v == 0 or v == default_handler or v in seen:
            continue
        seen.add(v)

        if i < 16:
            name = exc_names[i]
        else:
            irq = i - 16
            name = f"IRQ_{irq}"

        addr = v & 0xFFFFFFFE
        if APP_BASE <= addr < APP_BASE + len(data):
            print(f"  --- {name} (0x{v:08X}) ---")
            disassemble(data, addr, count=8)
            print()


def main():
    parser = argparse.ArgumentParser(description='Blackbox Firmware Disassembler')
    parser.add_argument('firmware', help='Path to .bin firmware file')
    parser.add_argument('--addr', '-a', type=lambda x: int(x, 0),
                        help='Address to disassemble (hex, e.g. 0x08040400)')
    parser.add_argument('--count', '-c', type=int, default=30,
                        help='Number of instructions (default: 30)')
    parser.add_argument('--function', '-f', action='store_true',
                        help='Disassemble entire function (stop at return)')
    parser.add_argument('--vectors', '-V', action='store_true',
                        help='Disassemble all vector table handlers')
    parser.add_argument('--base', '-b', type=lambda x: int(x, 0), default=APP_BASE,
                        help=f'Base address (default: 0x{APP_BASE:08X})')
    args = parser.parse_args()

    base = args.base

    data = Path(args.firmware).read_bytes()
    print(f"  Loaded {len(data):,} bytes from {args.firmware}")
    print(f"  Base address: 0x{base:08X}")
    print()

    # Override module-level constant for all functions
    _set_base(base)

    if args.vectors:
        show_vectors(data)
    elif args.addr:
        if args.function:
            print(f"  --- Function at 0x{args.addr:08X} ---")
            disassemble_function(data, args.addr)
        else:
            disassemble(data, args.addr, count=args.count)
    else:
        # Default: disassemble from reset handler
        reset = struct.unpack_from('<I', data, 4)[0]
        print(f"  --- Reset Handler (0x{reset:08X}) ---")
        disassemble(data, reset & 0xFFFFFFFE, count=args.count)


if __name__ == '__main__':
    main()
