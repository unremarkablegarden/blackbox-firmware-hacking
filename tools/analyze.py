#!/usr/bin/env python3
"""
Blackbox Firmware Analyzer
Parses STM32H7 firmware binaries: vector table, memory map, strings, structure.

Usage:
    python3 tools/analyze.py Firmwares/BLACKBOX312.bin
    python3 tools/analyze.py Firmwares/BLACKBOX312.bin --verbose
    python3 tools/analyze.py Firmwares/BLACKBOX312.bin --json
"""

import struct
import sys
import argparse
import json
from pathlib import Path

# STM32H7 memory regions
MEMORY_MAP = {
    "ITCM_FLASH": (0x00000000, 0x0000FFFF, "ITCM Flash alias"),
    "FLASH":      (0x08000000, 0x081FFFFF, "Internal flash (2MB)"),
    "ITCM_RAM":   (0x00000000, 0x0000FFFF, "Instruction TCM (64KB)"),
    "DTCM_RAM":   (0x20000000, 0x2001FFFF, "Data TCM (128KB)"),
    "AXI_SRAM":   (0x24000000, 0x2407FFFF, "AXI SRAM (512KB)"),
    "SRAM1":      (0x30000000, 0x3001FFFF, "SRAM1 (128KB)"),
    "SRAM2":      (0x30020000, 0x3003FFFF, "SRAM2 (128KB)"),
    "SRAM3":      (0x30040000, 0x30047FFF, "SRAM3 (32KB)"),
    "SRAM4":      (0x38000000, 0x3800FFFF, "SRAM4 (64KB)"),
    "PERIPH":     (0x40000000, 0x5FFFFFFF, "Peripherals"),
}

APP_BASE = 0x08040000  # Application load address (after 256KB bootloader)

# Standard Cortex-M7 exception names
EXCEPTION_NAMES = [
    "Initial SP", "Reset", "NMI", "HardFault", "MemManage", "BusFault",
    "UsageFault", "Reserved7", "Reserved8", "Reserved9", "Reserved10",
    "SVCall", "DebugMon", "Reserved13", "PendSV", "SysTick",
]

# STM32H7 IRQ names (subset — most relevant for audio device)
STM32H7_IRQS = {
    0: "WWDG", 1: "PVD_AVD", 2: "TAMP_STAMP", 3: "RTC_WKUP",
    4: "FLASH", 5: "RCC", 6: "EXTI0", 7: "EXTI1", 8: "EXTI2",
    9: "EXTI3", 10: "EXTI4", 11: "DMA1_Stream0", 12: "DMA1_Stream1",
    13: "DMA1_Stream2", 14: "DMA1_Stream3", 15: "DMA1_Stream4",
    16: "DMA1_Stream5", 17: "DMA1_Stream6", 18: "ADC", 19: "FDCAN1_IT0",
    20: "FDCAN2_IT0", 21: "FDCAN1_IT1", 22: "FDCAN2_IT1", 23: "EXTI9_5",
    24: "TIM1_BRK", 25: "TIM1_UP", 26: "TIM1_TRG_COM", 27: "TIM1_CC",
    28: "TIM2", 29: "TIM3", 30: "TIM4", 31: "I2C1_EV", 32: "I2C1_ER",
    33: "I2C2_EV", 34: "I2C2_ER", 35: "SPI1", 36: "SPI2",
    37: "USART1", 38: "USART2", 39: "USART3", 40: "EXTI15_10",
    41: "RTC_Alarm", 43: "TIM8_BRK_TIM12", 44: "TIM8_UP_TIM13",
    45: "TIM8_TRG_COM_TIM14", 46: "TIM8_CC", 47: "DMA1_Stream7",
    48: "FMC", 49: "SDMMC1", 50: "TIM5", 51: "SPI3", 52: "UART4",
    53: "UART5", 54: "TIM6_DAC", 55: "TIM7", 56: "DMA2_Stream0",
    57: "DMA2_Stream1", 58: "DMA2_Stream2", 59: "DMA2_Stream3",
    60: "DMA2_Stream4", 67: "DMA2_Stream5", 68: "DMA2_Stream6",
    69: "DMA2_Stream7", 70: "USART6", 71: "I2C3_EV", 72: "I2C3_ER",
    73: "OTG_HS_EP1_OUT", 74: "OTG_HS_EP1_IN", 75: "OTG_HS_WKUP",
    76: "OTG_HS", 77: "DCMI_PSSI", 80: "RNG", 81: "FPU",
    82: "UART7", 83: "UART8", 84: "SPI4", 85: "SPI5", 86: "SPI6",
    87: "SAI1", 88: "LTDC", 89: "LTDC_ER", 90: "DMA2D",
    91: "SAI2", 92: "QUADSPI", 93: "LPTIM1",
    95: "SDMMC2", 96: "SPI6", 102: "SAI3", 110: "MDMA",
    111: "SDMMC2", 124: "SAI4",
}


def identify_region(addr):
    """Identify which memory region an address belongs to."""
    for name, (start, end, desc) in MEMORY_MAP.items():
        if start <= addr <= end:
            return name, desc
    return "UNKNOWN", f"0x{addr:08X}"


def read_vector_table(data, count=160):
    """Read the ARM Cortex-M vector table."""
    vectors = []
    for i in range(min(count, len(data) // 4)):
        val = struct.unpack_from('<I', data, i * 4)[0]
        vectors.append(val)
    return vectors


def extract_strings(data, min_length=6):
    """Extract printable ASCII strings from binary data."""
    strings = []
    current = bytearray()
    offset = 0
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


def find_color_palette(data):
    """Find ARGB32 color palette entries (0xFFxxxxxx patterns in clusters)."""
    palettes = []
    i = 0
    while i < len(data) - 4:
        val = struct.unpack_from('<I', data, i)[0]
        if (val & 0xFF000000) == 0xFF000000 and val != 0xFFFFFFFF and val != 0xFF000000:
            # Potential color — check if part of a cluster
            cluster_start = i
            colors = []
            j = i
            gap = 0
            while j < len(data) - 4 and gap < 8:
                v = struct.unpack_from('<I', data, j)[0]
                if (v & 0xFF000000) == 0xFF000000:
                    colors.append((j, v))
                    gap = 0
                else:
                    gap += 4
                j += 4
            if len(colors) >= 8:  # Meaningful palette
                palettes.append(colors)
                i = j
            else:
                i += 4
        else:
            i += 4
    return palettes


def find_cpp_symbols(strings_list):
    """Find C++ class::method patterns in extracted strings."""
    symbols = []
    for offset, s in strings_list:
        if '::' in s and not s.startswith('//') and len(s) < 200:
            symbols.append((offset, s))
    return symbols


def find_build_paths(strings_list):
    """Find Windows/Unix build paths."""
    paths = []
    for offset, s in strings_list:
        if (':\\' in s or s.startswith('/')) and ('Projects' in s or 'Code' in s or 'Src' in s or '.cpp' in s or '.c' in s):
            paths.append((offset, s))
    return paths


def find_version_string(strings_list):
    """Find firmware version string."""
    for offset, s in strings_list:
        # Look for version patterns near "blackbox" or "1010music"
        if s.lower() in ('blackbox', 'bluebox', 'bitbox'):
            # Check nearby strings for version
            continue
    # Also look for x.y.z patterns
    import re
    for offset, s in strings_list:
        if re.match(r'^\d+\.\d+\.[0-9A-Za-z]+$', s):
            return offset, s
    return None, None


def compute_entropy(data, block_size=256):
    """Compute Shannon entropy of data."""
    import math
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    total = len(data)
    entropy = 0
    for f in freq:
        if f > 0:
            p = f / total
            entropy -= p * math.log2(p)
    return entropy


def analyze_firmware(path, verbose=False, output_json=False):
    """Main analysis routine."""
    data = Path(path).read_bytes()
    results = {}

    # --- Basic info ---
    results['file'] = {
        'path': str(path),
        'size_bytes': len(data),
        'size_kb': round(len(data) / 1024, 1),
        'entropy': round(compute_entropy(data), 3),
    }

    # --- Vector table ---
    vectors = read_vector_table(data, 160)
    initial_sp = vectors[0]
    reset_handler = vectors[1]
    sp_region, sp_desc = identify_region(initial_sp)
    reset_region, reset_desc = identify_region(reset_handler & 0xFFFFFFFE)

    results['vector_table'] = {
        'initial_sp': f"0x{initial_sp:08X}",
        'initial_sp_region': f"{sp_region} ({sp_desc})",
        'reset_handler': f"0x{reset_handler:08X}",
        'reset_handler_region': f"{reset_region} ({reset_desc})",
        'app_base': f"0x{APP_BASE:08X}",
    }

    # Active interrupt handlers (non-zero, not pointing to a common default handler)
    active_irqs = []
    default_handler = None
    handler_counts = {}
    for i in range(16, len(vectors)):
        v = vectors[i]
        if v != 0:
            handler_counts[v] = handler_counts.get(v, 0) + 1

    # The most common non-zero handler is likely the default handler
    if handler_counts:
        default_handler = max(handler_counts, key=handler_counts.get)

    for i in range(16, len(vectors)):
        v = vectors[i]
        irq_num = i - 16
        if v != 0 and v != default_handler:
            name = STM32H7_IRQS.get(irq_num, f"IRQ_{irq_num}")
            active_irqs.append({'irq': irq_num, 'name': name, 'handler': f"0x{v:08X}"})

    results['active_interrupts'] = active_irqs

    # --- Strings ---
    all_strings = extract_strings(data, min_length=6)
    results['strings'] = {
        'total_count': len(all_strings),
        'cpp_symbols': [(f"0x{o:06X}", s) for o, s in find_cpp_symbols(all_strings)],
        'build_paths': [(f"0x{o:06X}", s) for o, s in find_build_paths(all_strings)],
    }

    ver_offset, ver_string = find_version_string(all_strings)
    if ver_string:
        results['strings']['version'] = {'offset': f"0x{ver_offset:06X}", 'value': ver_string}

    # --- Color palette ---
    palettes = find_color_palette(data)
    if palettes:
        largest = max(palettes, key=len)
        results['color_palette'] = {
            'offset': f"0x{largest[0][0]:06X}",
            'count': len(largest),
            'colors': [f"0x{c:08X}" for _, c in largest],
        }

    # --- Protection check ---
    # Look for CRC32 tables and crypto signatures
    crc_poly_le = struct.pack('<I', 0xEDB88320)
    crc_poly_be = struct.pack('<I', 0x04C11DB7)
    has_crc = crc_poly_le in data or crc_poly_be in data

    crypto_strings = []
    for offset, s in all_strings:
        sl = s.lower()
        if any(kw in sl for kw in ['crc', 'checksum', 'signature', 'sha256', 'sha1', 'hmac', 'encrypt', 'decrypt', 'verify firmware']):
            crypto_strings.append(s)

    results['protection'] = {
        'crc32_table_found': has_crc,
        'crypto_strings_found': crypto_strings,
        'encrypted': results['file']['entropy'] > 7.9,
        'assessment': 'UNPROTECTED' if not has_crc and not crypto_strings else 'POSSIBLY PROTECTED',
    }

    # --- RTOS tasks ---
    rtos_indicators = []
    for offset, s in all_strings:
        if s in ('defaultTask', 'audioTask', 'pcmStreamer', 'IDLE', 'Tmr Svc', 'USBH_Thread'):
            rtos_indicators.append(s)
    results['rtos'] = {
        'likely_rtos': 'FreeRTOS' if rtos_indicators else 'Unknown',
        'task_names': rtos_indicators,
    }

    # --- Output ---
    if output_json:
        print(json.dumps(results, indent=2))
        return results

    # Pretty print
    f = results['file']
    print(f"{'='*60}")
    print(f"  BLACKBOX FIRMWARE ANALYSIS")
    print(f"{'='*60}")
    print(f"  File:     {f['path']}")
    print(f"  Size:     {f['size_bytes']:,} bytes ({f['size_kb']} KB)")
    print(f"  Entropy:  {f['entropy']} bits/byte", end="")
    print(f"  {'(compiled code — NOT encrypted)' if f['entropy'] < 7.9 else '(HIGH — possibly encrypted!)'}")
    print()

    vt = results['vector_table']
    print(f"  VECTOR TABLE")
    print(f"  Initial SP:     {vt['initial_sp']}  [{vt['initial_sp_region']}]")
    print(f"  Reset Handler:  {vt['reset_handler']}  [{vt['reset_handler_region']}]")
    print(f"  App Base Addr:  {vt['app_base']}")
    print()

    if ver_string:
        v = results['strings']['version']
        print(f"  VERSION: {v['value']}  (at offset {v['offset']})")
        print()

    print(f"  PROTECTION: {results['protection']['assessment']}")
    print(f"    CRC32 table:    {'FOUND' if results['protection']['crc32_table_found'] else 'Not found'}")
    print(f"    Crypto strings: {', '.join(results['protection']['crypto_strings_found']) or 'None'}")
    print(f"    Encrypted:      {'YES' if results['protection']['encrypted'] else 'No'}")
    print()

    print(f"  RTOS: {results['rtos']['likely_rtos']}")
    if results['rtos']['task_names']:
        for t in results['rtos']['task_names']:
            print(f"    - {t}")
    print()

    print(f"  ACTIVE INTERRUPT HANDLERS ({len(active_irqs)} custom):")
    for irq in active_irqs:
        print(f"    IRQ {irq['irq']:>3}  {irq['name']:<20}  → {irq['handler']}")
    print()

    print(f"  STRINGS: {results['strings']['total_count']} total (>= 6 chars)")
    print()

    if results['strings']['build_paths']:
        print(f"  BUILD PATHS:")
        for offset, p in results['strings']['build_paths']:
            print(f"    {offset}  {p}")
        print()

    if results['strings']['cpp_symbols']:
        print(f"  C++ SYMBOLS ({len(results['strings']['cpp_symbols'])}):")
        for offset, s in results['strings']['cpp_symbols'][:40]:
            print(f"    {offset}  {s}")
        if len(results['strings']['cpp_symbols']) > 40:
            print(f"    ... and {len(results['strings']['cpp_symbols']) - 40} more")
        print()

    if 'color_palette' in results:
        cp = results['color_palette']
        print(f"  COLOR PALETTE ({cp['count']} colors at {cp['offset']}):")
        for c in cp['colors'][:12]:
            r = (int(c, 16) >> 16) & 0xFF
            g = (int(c, 16) >> 8) & 0xFF
            b = int(c, 16) & 0xFF
            print(f"    {c}  RGB({r:3}, {g:3}, {b:3})")
        if cp['count'] > 12:
            print(f"    ... and {cp['count'] - 12} more")
        print()

    if verbose:
        print(f"  ALL STRINGS:")
        print(f"  {'─'*56}")
        for offset, s in all_strings:
            print(f"    0x{offset:06X}  {s}")

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Blackbox Firmware Analyzer')
    parser.add_argument('firmware', help='Path to .bin firmware file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print all strings')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    args = parser.parse_args()

    analyze_firmware(args.firmware, verbose=args.verbose, output_json=args.json)
