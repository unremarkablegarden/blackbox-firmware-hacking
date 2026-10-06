# 1010music Blackbox — Firmware Modding & Reverse Engineering Guide

## TL;DR

The Blackbox firmware is **highly moddable**. The `.bin` update files are raw, unprotected ARM Cortex-M7 binaries with no checksums, no signatures, and no encryption. You can patch the binary, drop it on an SD card, and flash it. Nobody in the community appears to have done serious modding work yet — you'd be a pioneer.

---

## Table of Contents

1. [Current State of Community Efforts](#1-current-state-of-community-efforts)
2. [Firmware Binary Analysis](#2-firmware-binary-analysis)
3. [What You Can Do Today (Easy)](#3-what-you-can-do-today-easy)
4. [Reverse Engineering the Firmware](#4-reverse-engineering-the-firmware)
5. [Patching & Modifying the Firmware](#5-patching--modifying-the-firmware)
6. [Hardware Access via SWD/JTAG](#6-hardware-access-via-swdjtag)
7. [Writing Custom Firmware from Scratch](#7-writing-custom-firmware-from-scratch)
8. [Precedents: Other Devices People Have Modded](#8-precedents-other-devices-people-have-modded)
9. [Risk Assessment & Brick Recovery](#9-risk-assessment--brick-recovery)
10. [Recommended Approach & Roadmap](#10-recommended-approach--roadmap)
11. [Tools & Resources](#11-tools--resources)

---

## 1. Current State of Community Efforts

**Nobody has publicly done this yet.** As of early 2025:

- No public firmware disassembly, teardown documentation, or modding projects exist on GitHub, Reddit, ModWiggler, Elektronauts, or Gearspace.
- No one has documented JTAG/SWD access to any 1010music product.
- No alternative firmware project exists.
- Community requests to open-source the firmware ([forum thread](https://forum.1010music.com/forum/products/blackbox/wish-list-blackbox/25793-open-the-sources)) have gone unanswered.
- The Blackbox community is primarily musicians, not embedded hackers.

The last firmware update (v3.12) was released **February 2024**. The 1010music forum has gone largely silent. The company's focus shifted entirely to the Bento (2025), which uses a completely new OS and hardware platform.

**You would be the first.** The good news: the technical barriers are surprisingly low.

---

## 2. Firmware Binary Analysis

Direct analysis of the three firmware files in `Firmwares/` reveals everything needed to start modding.

### File Properties

| File | Version | Date | Size | Growth |
|------|---------|------|------|--------|
| `Blackbox102.BIN` | 1.0.2 | 2019-04-26 | 458 KB | — |
| `BLACKBOX20E.bin` | 2.0.E | 2022-03-03 | 651 KB | +42% |
| `BLACKBOX312.bin` | 3.1.2 | 2024-02-20 | 680 KB | +4.4% |

### Protection Status: NONE

This is the single most important finding:

| Check | Result |
|-------|--------|
| **CRC32 appended?** | No — last 4 bytes are a `.bss` end address, not a checksum |
| **CRC32 table in binary?** | No — neither `0xEDB88320` nor `0x04C11DB7` polynomial found |
| **SHA/HMAC/signature?** | No — no crypto-related strings or constants |
| **Encryption?** | No — entropy is 7.37-7.43 bits/byte (compiled code), not ~8.0 (encrypted) |
| **Firmware header?** | No — file begins directly with the ARM vector table |
| **Update verification strings?** | None — no "CRC", "checksum", "verify", "invalid", "update failed" |

The firmware is a **raw flash image** with zero integrity protection. All update logic lives in the bootloader (first 256 KB of flash, not included in the `.bin`).

### Memory Layout

```
Flash Memory Map:
┌─────────────────────────────────────┐ 0x08000000
│  BOOTLOADER (256 KB)                │
│  NOT included in .bin files         │
│  Handles SD card update             │
├─────────────────────────────────────┤ 0x08040000  ← .bin loads here
│  APPLICATION FIRMWARE               │
│  Vector table at offset 0x000       │
│  Code + rodata                      │
│  Strings, UI text, XML templates    │
│  Initialized data (.data)           │
│  Color palette, config structs      │
│  0xAAAAAAAA section marker           │
│  Constructor init tables            │
│  .bss end pointer (last word)       │
└─────────────────────────────────────┘ ~0x080E9000 (v3.12)

RAM:
  AXI SRAM:  0x24000000 - 0x2407FFFF  (512 KB, stack + heap)
  DTCM:      0x20000000 - 0x2001FFFF  (128 KB)
  SRAM1-4:   0x30000000+              (various)
  Ext SDRAM: 64 MB (2 x 256 Mbit)
```

### Embedded Build Paths

```
C:\Projects\Code\matrixsw\BoomboxFramework\Src\usbh_conf.c
C:\Projects\Code\matrixsw\BoomboxFramework\Src\I2CPortBoombox.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\AnalogInput.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\AudioDriverBoombox.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\SDMgr.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\MidiPort.cpp
```

Developer `kf6gp` (Ray Rischpater) username appears in v2.0E paths.

### Key C++ Classes (from symbol strings)

```
PowerMgr::Shutdown          PowerMgr::SetLowPowerMode
SessionMgr::LoadBank        SessionMgr::FinalizeBankLoading
PresetMgr::RequestPresetLoad PresetMgr::SaveAs         PresetMgr::PackPreset
UIToolbar::InsertButton
WaveFileFF::WriteHeader     WaveFileFF::OpenWriteFile  WaveFileFF::PushData
BlamSliceVoice::StartNote   BlamSliceVoice::ProcessNote
BlamMVoicePool::GetVoice
BitmapFile::SaveToFile
```

### RTOS Tasks

| Task Name | Purpose |
|-----------|---------|
| `defaultTask` | Main application task (STM32CubeMX default) |
| `audioTask` | Real-time audio processing |
| `pcmStreamer` | PCM sample streaming from SD card |
| `USBH_Thread` | USB host stack |

---

## 3. What You Can Do Today (Easy)

These modifications require only a hex editor and the publicly available `.bin` file:

### Change UI Text & Menu Labels

All UI strings are plaintext ASCII at known offsets. You can:
- Fix typos or rename menu items
- Change the splash screen text (`"blackbox"`, `"by 1010music"`)
- Modify version string (`"3.1.2"` at offset `0x8CED4` in v3.12)
- Translate menu items

**Method**: Open in a hex editor, find the string, overwrite (keep same length or pad with nulls).

### Retheme the UI Colors

A 35-entry ARGB32 color palette sits near the end of the binary:

| Role | Current Color | Hex Value |
|------|--------------|-----------|
| Primary accent (cyan) | ![#09D7F5](https://via.placeholder.com/12/09D7F5/09D7F5.png) | `0xFF09D7F5` (appears 6x) |
| Active/positive (green) | ![#22BB22](https://via.placeholder.com/12/22BB22/22BB22.png) | `0xFF22BB22` |
| Alert/negative (red) | ![#BB2222](https://via.placeholder.com/12/BB2222/BB2222.png) | `0xFFBB2222` |
| Secondary accent (pink) | ![#FF6AF3](https://via.placeholder.com/12/FF6AF3/FF6AF3.png) | `0xFFFF6AF3` |
| Background (near-black) | ![#141414](https://via.placeholder.com/12/141414/141414.png) | `0xFF141414` |
| Text (white) | ![#FFFFFF](https://via.placeholder.com/12/FFFFFF/FFFFFF.png) | `0xFFFFFFFF` |
| Inactive (dark gray) | ![#666666](https://via.placeholder.com/12/666666/666666.png) | `0xFF666666` |
| Purple accent | ![#BA00FF](https://via.placeholder.com/12/BA00FF/BA00FF.png) | `0xFFBA00FF` |
| Mint accent | ![#00FFCC](https://via.placeholder.com/12/00FFCC/00FFCC.png) | `0xFF00FFCC` |

**Method**: Find the color values in the hex editor, replace with your preferred colors. Instant retheme.

### Modify Configuration Constants

Hardware config values (clock frequencies, SRAM sizes) are embedded as constants. Some behavioral parameters may also be exposed as modifiable data rather than code.

---

## 4. Reverse Engineering the Firmware

### Setting Up Ghidra (Free, Recommended)

1. **Download** Ghidra from ghidra-sre.org
2. **New Project** → Import File → select `BLACKBOX312.bin`
3. **Language**: `ARM:LE:32:Cortex` (ARM little-endian, 32-bit, Cortex)
4. **Options**: Set base address to `0x08040000`
5. **Auto-analyze** when prompted (accept all defaults)

### Memory Map Configuration

After import, go to `Window → Memory Map` and add:

| Region | Start | End | Size | Type |
|--------|-------|-----|------|------|
| ITCM RAM | `0x00000000` | `0x0000FFFF` | 64 KB | RAM |
| DTCM RAM | `0x20000000` | `0x2001FFFF` | 128 KB | RAM |
| AXI SRAM | `0x24000000` | `0x2407FFFF` | 512 KB | RAM |
| SRAM1 | `0x30000000` | `0x3001FFFF` | 128 KB | RAM |
| SRAM2 | `0x30020000` | `0x3003FFFF` | 128 KB | RAM |
| SRAM3 | `0x30040000` | `0x30047FFF` | 32 KB | RAM |
| SRAM4 | `0x38000000` | `0x3800FFFF` | 64 KB | RAM |
| Peripherals | `0x40000000` | `0x5FFFFFFF` | — | I/O |

### Essential Ghidra Plugin: SVD-Loader

Install the **SVD-Loader** plugin from GitHub. Import the STM32H743 or STM32H750 SVD file from [cmsis-svd](https://github.com/cmsis-svd/cmsis-svd-data). This auto-labels all peripheral registers:
- `GPIOA->MODER` instead of `*(0x40020000)`
- `SAI1->GCR` instead of `*(0x40015800)`
- `SDMMC1->DCTRL` instead of `*(0x52007000)`

This transforms unreadable peripheral access into self-documenting code.

### What to Look for First

1. **Vector table** (offset `0x000`): Maps all interrupt handlers. The SAI/DMA interrupts lead you to the audio pipeline.
2. **GPIO init code**: `HAL_GPIO_Init()` calls reveal every pin assignment on the board — this IS the schematic.
3. **FreeRTOS task creation**: Search for `xTaskCreate` calls and task name strings to map the system architecture.
4. **Audio pipeline**: Follow the SAI/I2S peripheral init → DMA setup → audio callback → mixer/effects chain.
5. **UI rendering**: The touchscreen display code will reference the LTDC or SPI peripheral and the color palette.

### Alternative Disassemblers

| Tool | Cost | Notes |
|------|------|-------|
| **IDA Pro** | $1,500+ | Best decompiler output. IDA Free has cloud decompiler. |
| **Binary Ninja** | $300+ | Excellent intermediate representations (MLIL/HLIL). |
| **radare2/Cutter** | Free | Steep learning curve but fully capable. `r2 -a arm -b 32 -m 0x08040000 BLACKBOX312.bin` |

### Quick Command-Line Analysis

```bash
# Disassemble first 100 instructions
arm-none-eabi-objdump -D -b binary -m arm -M force-thumb \
  --start-address=0 --stop-address=0x200 BLACKBOX312.bin

# Extract all strings (8+ chars)
strings -n 8 BLACKBOX312.bin | less

# Check for embedded filesystems or compressed sections
binwalk BLACKBOX312.bin

# Hex dump the vector table
xxd -l 256 BLACKBOX312.bin
```

---

## 5. Patching & Modifying the Firmware

### Data-Level Patches (Simple)

These modify data, not code. Low risk, easy to verify.

**Workflow:**
1. Find the data in a hex editor (strings, colors, constants)
2. Modify in place (keep same byte count — pad with `0x00` if shorter)
3. Save as new `.bin` file
4. Copy to SD card root
5. Power on holding the appropriate button combo to trigger update

### Code-Level Patches (Intermediate)

Modify program behavior by changing instructions.

**Common techniques:**

| Technique | Description | Example |
|-----------|-------------|---------|
| **NOP out** | Replace instruction with NOP (`0xBF00` for 2-byte, `0xF3AF 0x8000` for 4-byte) | Skip a check, disable a feature |
| **Flip a branch** | Change `BEQ` → `BNE` or `BEQ` → `B` (unconditional) | Invert a condition, always/never take a path |
| **Change immediate** | Modify a constant loaded by `MOV` or `LDR` | Change a limit (max voices, max effects, etc.) |
| **Redirect a call** | Change the target of a `BL` instruction | Hook a function to call your code instead |

**Example: Changing a polyphony limit**
```
; Original: MOV R0, #24    (max voices = 24)
; Patched:  MOV R0, #32    (max voices = 32)
; Find the instruction bytes, change the immediate field
```

### Adding New Code (Advanced)

For larger modifications, you need space for new code:

1. **Find unused flash** — look for runs of `0xFF` bytes (erased flash) between the end of the firmware and the next flash sector boundary
2. **Write your code** as a standalone function in ARM Thumb-2 assembly or C (compiled separately)
3. **Insert it** into the unused space
4. **Hook it** by replacing a `BL` (branch-with-link) at the call site to point to your new code
5. Your new code can call the original function and/or add behavior

The `BL` instruction in Thumb-2 has a ±16 MB range — more than enough to reach anywhere in flash.

### Using Ghidra for Patching

Ghidra can both analyze and patch:
1. Right-click an instruction → `Patch Instruction`
2. Modify it in the assembler dialog
3. `File → Export Program → Binary` to save the patched version

---

## 6. Hardware Access via SWD/JTAG

Opening the device gives you much more power than software-only modding.

### What You Need

| Item | Cost | Purpose |
|------|------|---------|
| **Debug probe** (ST-Link V3 or J-Link EDU) | $35-60 | Connect to the MCU's debug port |
| **Fine-pitch probe wires or pogo pins** | $10-20 | Reach SWD test points on the PCB |
| **Multimeter** | (you probably have one) | Trace connections, verify voltages |

### SWD Pins on STM32H7

| Signal | Default Pin | Purpose |
|--------|-------------|---------|
| SWDIO | PA13 | Bidirectional data |
| SWCLK | PA14 | Clock |
| GND | — | Ground reference |
| VTref | 3.3V | Voltage reference for probe |
| NRST | NRST pin | Reset (optional but useful) |

Look for **unpopulated header holes**, **test points**, or **labeled pads** on the PCB. Most manufacturers leave SWD accessible for production programming even without a connector.

### First Steps After Connecting

```bash
# Using STM32CubeProgrammer CLI — read option bytes (non-destructive)
STM32_Programmer_CLI -c port=SWD -ob displ

# This tells you:
# - RDP level (0, 1, or 2)
# - Write protection settings
# - Secure area configuration
# - Boot configuration
```

### Read Protection Scenarios

| RDP Level | What Happens | What You Can Do |
|-----------|-------------|-----------------|
| **Level 0** | Full access. Read flash, RAM, set breakpoints, single-step. | Everything. Dump flash, live debug, write custom firmware. |
| **Level 1** | SWD connects but flash reads are blocked. | Mass-erase to return to Level 0 (loses flash contents — but you have the .bin). Then reflash from SD card. |
| **Level 2** | Debug port permanently disabled. Irreversible. | Software-only modding via SD card updates. No debug access ever. |

**Prediction**: RDP Level 0 or 1 is most likely. The firmware is publicly distributed, so there's little reason to lock it down. Level 2 is very rare on small-company audio products because it's irreversible and terrifies production engineers.

### If RDP Level 0: Full Dump

```bash
# Dump entire flash including bootloader
STM32_Programmer_CLI -c port=SWD -r 0x08000000 0x200000 full_flash_dump.bin

# Or with OpenOCD
openocd -f interface/stlink.cfg -f target/stm32h7x.cfg \
  -c "init; halt; flash read_image dump.bin 0x08000000 0x200000 bin; shutdown"
```

This gets you the **bootloader** (first 256 KB) — the one piece not in the public `.bin` files. Analyzing the bootloader reveals exactly how it validates firmware updates (if at all).

### Voltage Glitching (if RDP Level 1)

If Level 1 blocks you, voltage glitching can bypass it:
- **Tool**: ChipWhisperer Lite (~$250) or Husky (~$550)
- **Technique**: Inject a voltage glitch on VDD during the boot sequence when the MCU reads the RDP option byte, causing it to misread Level 1 as Level 0
- **Difficulty**: Moderate — requires trial-and-error to find the timing window
- **Precedent**: wallet.fail demonstrated this on STM32F at CCC 2018; ChipWhisperer has published STM32 glitching tutorials
- **Probably unnecessary**: Since you already have the firmware `.bin`, glitching is only needed to extract the bootloader or runtime secrets

---

## 7. Writing Custom Firmware from Scratch

This is the most ambitious path but entirely feasible thanks to the **Electrosmith Daisy** platform.

### The Daisy Connection

The [Electrosmith Daisy Seed](https://www.electro-smith.com/daisy) is an open-source audio platform that uses the **exact same processor** as the Blackbox:

| Spec | Daisy Seed | Blackbox |
|------|-----------|----------|
| **MCU** | STM32H750 | STM32H7xx (likely H750 or H743) |
| **Core** | Cortex-M7 @ 480 MHz | Cortex-M7 @ 480 MHz |
| **External RAM** | 64 MB SDRAM | 64 MB SDRAM |
| **Audio** | 24-bit / 96 kHz | 24-bit / 48 kHz |
| **License** | MIT | Proprietary |

Daisy's **libDaisy** (hardware abstraction) and **DaisySP** (DSP library) are fully open-source, MIT-licensed, and provide:
- Audio I/O (I2S/SAI codec driver)
- SD card (FatFS)
- Display drivers
- USB MIDI
- SDRAM management

**If you identify the Blackbox's pin mappings** (from disassembly or physical probing), you could potentially port libDaisy to run on the Blackbox hardware.

### Extracting Pin Mappings from the Firmware

The firmware disassembly is your schematic:
1. Find `HAL_GPIO_Init()` calls — each one configures a pin with mode, pull, speed, and **alternate function**
2. The alternate function number maps to a specific peripheral (cross-reference with STM32H7 datasheet Table 9 "Alternate function mapping")
3. Find peripheral init: `HAL_SAI_Init()`, `HAL_SD_Init()`, `HAL_SPI_Init()`, `HAL_I2C_Init()`
4. Document every pin → peripheral mapping

This gives you the complete hardware interface without ever picking up a multimeter.

### Toolchain for Custom Firmware

| Component | Option | Notes |
|-----------|--------|-------|
| **IDE** | STM32CubeIDE (free) | Full Eclipse-based IDE with debugger, CubeMX pin configurator |
| **Compiler** | arm-none-eabi-gcc | `brew install arm-none-eabi-gcc` on macOS |
| **Build** | CMake or Make | STM32CubeIDE generates Makefiles |
| **RTOS** | FreeRTOS | Match the original, or go bare-metal |
| **HAL** | STM32 HAL or LL drivers | Included in STM32Cube packages |
| **Audio DSP** | DaisySP, CMSIS-DSP, or custom | MIT-licensed DSP building blocks |
| **Filesystem** | FatFS | Standard for STM32 + SD card |

### Build Incrementally

1. Blinky LED (verify basic MCU control)
2. UART output (for debugging)
3. Display init (prove you can drive the screen)
4. SD card mount (FatFS)
5. Audio codec init (I2S/SAI + DMA)
6. Audio passthrough (input → output)
7. Sample playback from SD card
8. Touch input
9. MIDI
10. Build your dream sampler

---

## 8. Precedents: Other Devices People Have Modded

### Synthstrom Deluge — The Gold Standard

- **What**: Standalone groovebox/sampler/synth
- **Processor**: Renesas RZ/A1 (ARM Cortex-A9)
- **Story**: Officially **open-sourced in June 2023** (GPLv3) after years of community requests. Community firmware v1.0 shipped within 6 months. Patreon-funded contributors now maintain and extend it.
- **Lesson**: The strongest argument for lobbying 1010music. Community open-sourcing saved a product from abandonment.

### Mutable Instruments — Open Source Eurorack

- **What**: All Eurorack modules (Clouds, Plaits, Rings, Beads, etc.)
- **Processor**: Various STM32 (F3, F4, H7)
- **Story**: Émilie Gillet open-sourced all firmware (MIT license). High-quality DSP code. After Mutable closed in 2022, the community continued developing and cloning.
- **Lesson**: STM32-based audio DSP algorithms (granular, wavetable, reverbs) that could be **directly ported** to the Blackbox.

### Electrosmith Daisy — Same Chip, Open Platform

- **What**: Open-source audio development platform
- **Processor**: STM32H750 (same as Blackbox)
- **Story**: Fully open hardware and software. Hundreds of community projects.
- **Lesson**: Proves the STM32H7 is a mature, well-supported platform for audio. Code is directly portable.

### Dirtywave M8 — Community Through Openness

- **What**: Portable tracker/groovebox
- **Processor**: Teensy 4.1 (Cortex-M7 @ 600 MHz)
- **Story**: Released headless firmware (no source, but precompiled binaries for generic hardware). Enabled a massive DIY community without revealing proprietary code.
- **Lesson**: Even partial openness creates thriving communities. 1010music could release a headless Blackbox build.

### Teenage Engineering OP-1 — Firmware Repacking

- **What**: Portable synthesizer/sampler
- **Story**: The `op1repacker` tool unpacks, modifies, and repacks OP-1 firmware files. Users changed graphics, sounds, and some behavior without source code access.
- **Lesson**: Directly applicable technique. A "blackbox-repacker" tool could do the same for the Blackbox `.bin` files.

### Korg logue SDK — Sandboxed Plugins

- **What**: Plugin SDK for Prologue, Minilogue XD, NTS-1
- **Story**: Users write custom oscillators and effects as plugins. Core firmware stays closed, but the plugin API allows deep customization.
- **Lesson**: A lower-risk model 1010music could adopt without open-sourcing core code.

### Akai MPC — Linux-Level Hacking

- **What**: MPC Live, MPC X, Force
- **Processor**: ARM Cortex-A (runs Linux)
- **Story**: Extensively hacked via SSH access, device spoofing, cross-product firmware swapping.
- **Lesson**: Linux-based devices are fundamentally easier to hack than bare-metal (like the Blackbox).

---

## 9. Risk Assessment & Brick Recovery

### Can You Brick It?

| Scenario | Risk | Recovery |
|----------|------|----------|
| **Bad .bin on SD card** | Low | The bootloader lives in a separate flash region (first 256 KB) and is NOT overwritten by firmware updates. If a bad firmware crashes, just power off, put a good `.bin` on the SD card, and update again. |
| **Corrupted bootloader via SWD** | High | If you accidentally overwrite the bootloader via debug probe, the device won't boot or accept SD card updates. Recovery requires reflashing the bootloader via SWD (you'd need a backup). |
| **RDP Level 2 set accidentally** | Catastrophic | Debug port permanently disabled. Irreversible. **Never write option bytes without understanding exactly what you're doing.** |
| **Bad peripheral config via custom firmware** | Low-Medium | Misconfigured GPIOs could theoretically damage the audio codec or display, but this is unlikely with normal experimentation. |

### Safety Rules

1. **Always keep a known-good `.bin`** on hand (the official v3.12)
2. **Dump the full flash (including bootloader) via SWD before modifying anything** — this is your insurance
3. **Never write option bytes** unless you fully understand RDP implications
4. **Never use `--force` or mass-erase** on the bootloader region
5. **Test patches incrementally** — change one thing at a time

### The SD Card Bootloader is Your Safety Net

The Blackbox bootloader checks for a firmware `.bin` file on the SD card at every boot. This means:
- A bad firmware patch just means a crash or freeze
- You can always recover by putting the original `.bin` back on the SD card
- The bootloader itself is never touched by normal firmware updates

This makes the Blackbox **much safer to mod** than devices with combined bootloader+application images.

---

## 10. Recommended Approach & Roadmap

### Phase 1: Analysis (No Hardware Risk)

**Time: A few days to weeks depending on experience**

1. Install Ghidra. Load `BLACKBOX312.bin` at base address `0x08040000`, ARM Cortex-M7.
2. Install SVD-Loader plugin with STM32H743/H750 SVD file.
3. Map out the architecture:
   - Identify the vector table and all interrupt handlers
   - Find FreeRTOS task creation points
   - Map the audio pipeline (SAI init → DMA → audio callback → effects)
   - Document GPIO pin assignments from `HAL_GPIO_Init()` calls
   - Understand the UI framework (display driver, touch handler, menu system)
4. Build a symbol map — name every function and class you identify.

### Phase 2: Cosmetic Mods (Zero Risk)

**Time: Hours**

1. Change the color palette in a hex editor
2. Modify UI strings (menu labels, splash screen)
3. Flash via SD card and verify
4. **Celebrate** — you've successfully modded your Blackbox

### Phase 3: Behavioral Patches (Low Risk)

**Time: Days to weeks**

1. Identify the function responsible for the bug you want to fix
2. Understand the logic in Ghidra's decompiler view
3. Craft a binary patch (NOP, branch flip, or constant change)
4. Use Ghidra's patch instruction feature or a hex editor
5. Flash and test

### Phase 4: Hardware Access (Optional, Moderate Risk)

**Time: An afternoon for initial connection**

1. Open the Blackbox (likely Phillips/Torx screws)
2. Photograph the PCB — both sides, high resolution
3. Identify the MCU part number from chip markings
4. Locate SWD test points (look near the MCU for PA13/PA14 pads)
5. Connect ST-Link V3 or J-Link EDU
6. Read option bytes to determine RDP level
7. If Level 0: dump full flash including bootloader — **this is your most important backup**
8. Set up live debugging (GDB + OpenOCD/J-Link)

### Phase 5: Custom Firmware (Ambitious)

**Time: Weeks to months**

1. Use pin mappings from Phase 1 disassembly
2. Set up STM32CubeIDE project for the identified H7 variant
3. Port libDaisy or write drivers from scratch
4. Build incrementally: display → SD card → audio → touch → MIDI
5. Create your dream sampler firmware

---

## 11. Tools & Resources

### Disassembly & Reverse Engineering

| Tool | Cost | URL |
|------|------|-----|
| Ghidra | Free | ghidra-sre.org |
| SVD-Loader (Ghidra plugin) | Free | github.com search "ghidra svd loader" |
| IDA Free | Free | hex-rays.com/ida-free |
| Binary Ninja | $300+ | binary.ninja |
| radare2 / Cutter | Free | rada.re |
| binwalk | Free | github.com/ReFirmLabs/binwalk |

### STM32 Development

| Tool | Cost | URL |
|------|------|-----|
| STM32CubeIDE | Free | st.com/stm32cubeide |
| STM32CubeProgrammer | Free | st.com/stm32cubeprog |
| arm-none-eabi-gcc | Free | developer.arm.com |
| OpenOCD | Free | openocd.org |
| STM32H7 Reference Manual (RM0433) | Free | st.com |
| STM32H7 Datasheet | Free | st.com |
| CMSIS-SVD files | Free | github.com/cmsis-svd/cmsis-svd-data |

### Debug Probes

| Probe | Cost | Notes |
|-------|------|-------|
| ST-Link V3 | ~$35 | Best value for STM32 work |
| SEGGER J-Link EDU | ~$60 | Fastest, best GDB server |
| Black Magic Probe | ~$40-75 | Open-source, native GDB |

### Audio DSP Libraries (Open Source)

| Library | License | Notes |
|---------|---------|-------|
| DaisySP | MIT | DSP for STM32H7, same chip family |
| libDaisy | MIT | HAL for Daisy/STM32H750 |
| CMSIS-DSP | Apache 2.0 | ARM's official DSP library |
| Mutable Instruments code | MIT | Battle-tested eurorack DSP |
| Faust | GPL | DSP programming language, compiles to C++ |

### Community & Reference

| Resource | URL |
|----------|-----|
| 1010music Forum | forum.1010music.com |
| Elektronauts Blackbox thread | elektronauts.com |
| ModWiggler | modwiggler.com |
| r/synthesizers | reddit.com/r/synthesizers |
| Daisy Forum | forum.electro-smith.com |
| ChipWhisperer (glitching) | newae.com/chipwhisperer |

---

*This report is based on direct binary analysis of Blackbox firmware files (v1.02, v2.0E, v3.12) and research across community forums, open-source projects, and STM32 documentation. The Blackbox is among the most moddable commercial samplers due to its unprotected firmware, standard MCU platform, and SD card update mechanism.*
