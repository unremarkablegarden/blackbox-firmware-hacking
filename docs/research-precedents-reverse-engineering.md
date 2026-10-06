# Precedents: Music Hardware Reverse Engineering & Open Source Firmware

Research into devices that have been reverse-engineered, received community firmware, or were officially open-sourced -- with lessons applicable to the 1010music Blackbox (STM32H7-based sampler).

---

## Table of Contents

1. [Officially Open-Sourced Devices](#1-officially-open-sourced-devices)
2. [Devices with Official Plugin/SDK Ecosystems](#2-devices-with-official-pluginsdk-ecosystems)
3. [Community-Reverse-Engineered Devices](#3-community-reverse-engineered-devices)
4. [Open Source Platforms That Could Port to Blackbox Hardware](#4-open-source-platforms-that-could-port-to-blackbox-hardware)
5. [Lessons and Applicability to the Blackbox](#5-lessons-and-applicability-to-the-blackbox)
6. [STM32 Read Protection Considerations](#6-stm32-read-protection-considerations)

---

## 1. Officially Open-Sourced Devices

### 1.1 Synthstrom Deluge -- The Gold Standard Precedent

| Attribute | Detail |
|---|---|
| **Device** | Synthstrom Audible Deluge -- groovebox/sampler/synth/sequencer |
| **Processor** | Renesas RZ/A1L (ARM Cortex-A9, 400 MHz) with 64 MB SDRAM |
| **Open-sourced** | June 2023, officially by the manufacturer |
| **License** | GPLv3 |
| **Source** | [github.com/SynthstromAudible/DelugeFirmware](https://github.com/SynthstromAudible/DelugeFirmware) |

**What the community accomplished:**
- Community Firmware 1.0 "Amadeus" released December 2023 -- six months after open-sourcing
- Major new features: master compressor, stereo chorus, grain synthesis, automation lanes, wavefold distortion, drum keyboard view, grid view
- Quarterly community releases with rigorous beta testing
- Dozens of contributors on GitHub (@0beron, @alter-alter, @bfredl, @bobtwinkles, etc.)

**Structure and governance:**
- Synthstrom maintains the "Official" repository for official releases
- A separate "Community" repository is the central place for community contributions
- An open-source project manager oversees the community repo
- A Patreon fund distributes 100% of donations (minus fees) to contributing coders, proportional to contribution volume

**Key lessons for Blackbox:**
- The Deluge is the single best model for what an open-sourced Blackbox could look like
- The manufacturer's willingness was the decisive factor -- no reverse engineering was needed
- Bare-metal C/C++ firmware (no OS) was successfully opened, just like the Blackbox's FreeRTOS/C++ stack
- Community firmware does NOT void the hardware warranty (only software support is excluded)
- Financial model (Patreon) sustains contributor motivation
- The fear that open-sourcing kills hardware sales proved unfounded -- it arguably increased the device's desirability

**Differences from Blackbox:**
- The Deluge uses a Cortex-A9 (application processor), not a Cortex-M7 (microcontroller) -- but both are bare-metal C++ with no Linux, so the development model is very similar
- Synthstrom is a smaller, more community-oriented company than 1010music

---

### 1.2 Dirtywave M8 Tracker -- Open Firmware on Teensy

| Attribute | Detail |
|---|---|
| **Device** | Dirtywave M8 -- portable tracker/synthesizer/sampler |
| **Processor** | Teensy 4.1 (NXP i.MX RT1062, ARM Cortex-M7, 600 MHz) |
| **Open-sourced** | Partially -- "Headless" firmware is open/redistributable; full device firmware is available as precompiled binary |
| **Source** | [github.com/Dirtywave/M8HeadlessFirmware](https://github.com/Dirtywave/M8HeadlessFirmware) |

**What the community accomplished:**
- M8 Headless: anyone can flash M8 firmware onto a bare Teensy 4.1 and use it with a computer as the display
- Cross-platform display clients: [m8c](https://github.com/laamaa/m8c) (C/SDL2), M8WebDisplay (Web Serial API), M8 Android client
- Massive DIY community building custom enclosures and hardware around the Teensy running M8 firmware
- The headless version served as a bridge when the hardware was perpetually sold out

**Key lessons for Blackbox:**
- The M8 uses the *same ARM Cortex-M7 core family* as the Blackbox (though a different chip vendor -- NXP vs ST)
- Releasing firmware binaries for generic hardware (Teensy) did NOT kill hardware sales -- demand was so high the device was perpetually backordered
- Even partial openness (precompiled firmware, not full source) enabled a thriving community
- The display-protocol approach (device sends pixels over USB, host renders) could inspire Blackbox remote-display hacks

---

### 1.3 Mutable Instruments -- The Open Source Eurorack Standard

| Attribute | Detail |
|---|---|
| **Device** | Entire Mutable Instruments Eurorack module line (Plaits, Clouds, Rings, Braids, Elements, etc.) |
| **Processor** | Various STM32F series (STM32F373, STM32F405, STM32F072, etc.) -- ARM Cortex-M4/M0 |
| **Open-sourced** | From the beginning by founder Emilie Gillet; all sources released before company closure in 2022 |
| **License** | MIT (STM32F projects), GPL3.0 (AVR projects) |
| **Source** | [github.com/pichenettes/eurorack](https://github.com/pichenettes/eurorack) |

**What the community accomplished:**
- Hundreds of DIY clones of every module (community and commercial)
- Custom firmware forks with additional modes and features (e.g., expanded Braids modes, alternative Clouds firmwares)
- Porting of Mutable DSP algorithms to other platforms (Korg logue SDK, VCV Rack, Daisy, etc.)
- Complete development environment scripts for building firmware
- The stmlib helper library became a de facto STM32 audio project template

**Key lessons for Blackbox:**
- These are STM32-based, C++ DSP projects -- the closest architectural match to the Blackbox
- Mutable's DSP algorithms (oscillators, filters, reverbs, granular processors) are proven, high-quality, and ready to port
- The MIT license means Mutable's DSP code could legally be incorporated into a Blackbox alternative firmware
- Mutable proved that open source hardware/firmware creates lasting cultural value in the music tech world

---

### 1.4 Axoloti -- Open Source Synth Platform on STM32

| Attribute | Detail |
|---|---|
| **Device** | Axoloti Core -- open hardware modular synth platform |
| **Processor** | STM32F427 (ARM Cortex-M4F, 168 MHz) |
| **Open-sourced** | From inception (Kickstarter 2015) by Johannes Taelman |
| **License** | CC-BY-SA (hardware), GPL (software) |

**What the community accomplished:**
- Visual patching environment (Java-based Axoloti Patcher) that generates C++ code, compiles with GCC, and uploads to the board
- Hundreds of community-contributed audio "objects" (filters, oscillators, sequencers, effects)
- Most Mutable Instruments oscillators ported to Axoloti objects
- Successor project "Ksoloti" continuing development after original went dormant

**Key lessons for Blackbox:**
- Demonstrates a complete open-source audio toolchain on the STM32 platform
- The Cortex-M4F at 168 MHz accomplished impressive DSP -- the Blackbox's Cortex-M7 at 480 MHz has roughly 5-6x more processing power
- Community of musicians (not just engineers) can contribute when the tooling is accessible
- The patching/visual approach lowered the barrier vs. writing raw C++

---

## 2. Devices with Official Plugin/SDK Ecosystems

### 2.1 Korg logue SDK (NTS-1, Prologue, minilogue xd, drumlogue)

| Attribute | Detail |
|---|---|
| **Device** | Korg NTS-1, Prologue, minilogue xd, NTS-1 mkII, NTS-3, microKORG2, drumlogue |
| **Processor** | Various (NTS-1: STM32F4 for main + Cortex-M4 for user oscillators) |
| **Approach** | Official SDK for user-developed oscillators, effects, and reverbs -- runs in a sandboxed environment |
| **Source** | [github.com/korginc/logue-sdk](https://github.com/korginc/logue-sdk) |

**What the community accomplished:**
- Hundreds of custom oscillators and effects on community sites (patchstorage.com)
- Mutable Instruments Plaits modes ported as NTS-1 oscillators
- Hardware mods: custom panels, Eurorack integration, ESP32-based custom controllers
- NTS-1 became a platform rather than just a product

**Key lessons for Blackbox:**
- Korg's approach is "sandboxed openness" -- you can add oscillators/effects but can't modify the core firmware
- This is a safer model for manufacturers worried about IP (1010music could adopt this)
- The SDK approach doesn't require opening the full firmware source
- Even a limited plugin system dramatically increased the NTS-1's longevity and community engagement

---

## 3. Community-Reverse-Engineered Devices

### 3.1 Akai MPC Live/X/Force/One -- Linux-Based, Extensively Hacked

| Attribute | Detail |
|---|---|
| **Device** | Akai MPC Live, MPC X, MPC One, MPC Key 61, Akai Force |
| **Processor** | Rockchip RK3288 (quad-core ARM Cortex-A17, 1.8 GHz), 2 GB RAM, 16 GB eMMC |
| **OS** | Linux (buildroot, kernel 4.4.80, glibc 2.22) |
| **Approach** | Community reverse engineering, NO manufacturer cooperation |

**Major projects:**
- [MPC-LiveXplore (TheKikGen)](https://github.com/TheKikGen/MPC-LiveXplore): SSH access, bootstrap images, device identity spoofing, extended button/pad mapping
- [Hakai](https://github.com/henning/Hakai-MPC): Dual-boot firmware allowing MPC devices to run Akai Force software (cross-product firmware swapping)
- [MockbaMod](https://github.com/MockbaTheBorg/MockbaMod): Scene automation and foot controller support for Force

**Techniques used:**
- Firmware image analysis to find Linux filesystem
- SSH activation through modified update images
- Device identity spoofing via `mount -o bind` to trick software into thinking it's running on different hardware
- VNC remote access for screen mirroring
- rtpmidi module for MIDI over Ethernet

**Key lessons for Blackbox:**
- The MPC runs Linux -- a fundamentally different (and easier) target than the Blackbox's bare-metal FreeRTOS firmware
- Linux devices have standard attack surfaces (SSH, filesystem, known tools) that bare-metal MCUs do not
- Cross-product firmware swapping (Hakai) is directly analogous to 1010music's own firmware-swapping feature between Bitbox/Fxbox/Synthbox
- The MPC hacking community discovered unreleased hardware (MPC XL) in firmware strings -- similar to how Blackbox firmware analysis revealed internal codenames and developer identities

---

### 3.2 Teenage Engineering OP-1 -- Firmware Repacking

| Attribute | Detail |
|---|---|
| **Device** | Teenage Engineering OP-1 -- portable synth/sampler/sequencer |
| **Processor** | Custom DSP + ARM (exact specs closely guarded by TE) |
| **Approach** | Community reverse engineering of firmware update files |

**Major project:**
- [op1repacker](https://github.com/op1hacks/op1repacker): Python tool for unpacking, modifying, and repacking OP-1 firmware
- [op1-fw-archive](https://github.com/op1hacks/op1-fw-archive): Archive of (almost) all OP-1 firmware versions
- [op1dumps](https://github.com/Tolsi/op1dumps): Hardware-level research (processor/flash replacement)

**What the community accomplished:**
- Unpack firmware, modify parameters (effect intensity defaults, graphics), repack as valid installable file
- Extract build metadata (version, date, bootloader version)
- Custom graphics (tape screen inversion, alternative graphics)
- Parameter tweaks (subtle effects mode)
- Firmware archiving for downgrade capability

**Techniques used:**
- Firmware file format analysis
- Python-based unpack/repack tooling
- Parameter identification through binary diffing between versions
- Graphics asset extraction and replacement

**Key lessons for Blackbox:**
- Even without full source code, firmware repacking enables useful modifications
- The Blackbox firmware is distributed as `.bin` files on SD card -- a similar attack surface to the OP-1's update mechanism
- Graphics, preset defaults, and parameter ranges are low-hanging fruit for modification
- WARNING: OP-1 custom firmware voids warranty and risks bricking

---

### 3.3 Roland AIRA Modular -- Reverse Engineering DSP Modules

| Attribute | Detail |
|---|---|
| **Device** | Roland AIRA Modular Effects (TORCIDO, BITRAZER, DEMORA, SCOOPER) |
| **Approach** | Mix of official SDK (AIRA Modular Customizer) and community reverse engineering |

**Key project:**
- [AIRA_Modular_Effects](https://github.com/mugenkidou/AIRA_Modular_Effects): Reverse engineering of the signal processing architecture
- Roland also released the official AIRA Modular Customizer for re-patching internal signal paths

**Key lessons for Blackbox:**
- Roland took a middle path: they provided an official customization tool while the community independently reverse-engineered the internals
- The AIRA modules likely use identical hardware with different firmware -- directly analogous to 1010music's Series 1 modules (Bitbox/Fxbox/Synthbox)

---

## 4. Open Source Platforms That Could Port to Blackbox Hardware

If someone gained low-level access to the Blackbox hardware (via SWD debug port or a bootloader exploit), these open-source projects contain code that could theoretically be adapted to run on the STM32H7:

### 4.1 Electrosmith Daisy (libDaisy + DaisySP) -- CLOSEST MATCH

| Attribute | Detail |
|---|---|
| **Processor** | **STM32H750** (ARM Cortex-M7, 480 MHz) -- essentially the **same chip family as the Blackbox** |
| **RAM** | 64 MB SDRAM -- **same as the Blackbox** |
| **Audio** | AKM stereo codec, 24-bit up to 192 kHz |
| **Source** | [github.com/electro-smith/libDaisy](https://github.com/electro-smith/libDaisy), [github.com/electro-smith/DaisySP](https://github.com/electro-smith/DaisySP) |
| **License** | MIT |

**Why this is the most relevant:**
- **Same MCU family** (STM32H7), same core (Cortex-M7), same clock speed (480 MHz), same external RAM size (64 MB)
- libDaisy provides: audio driver (I2S/SAI), SD card (FatFS), USB, MIDI, ADC, DAC, display drivers
- DaisySP provides: oscillators, filters, delays, reverbs, compressors, granular processors, sample playback
- MIT license means code can be freely adapted

**What would need adaptation for Blackbox hardware:**
- Pin mapping and peripheral configuration (different PCB layout)
- Audio codec driver (Blackbox likely uses a different codec than AKM)
- Display driver (Blackbox uses a 480x320 TFT; Daisy typically uses smaller OLEDs)
- Touch input handling
- The Blackbox's specific FreeRTOS task architecture

**This is the single most promising codebase for alternative Blackbox firmware.**

---

### 4.2 Mutable Instruments DSP Code

- High-quality DSP algorithms (granular, wavetable, FM, physical modeling, reverbs, filters)
- Already written for STM32 + GCC toolchain
- MIT licensed (STM32F projects)
- Would need porting from STM32F4 to STM32H7 (different peripheral registers, but same ARM core concepts)
- Could provide the synthesis engines for an alternative firmware

---

### 4.3 OTTO -- Open Source Groovebox (Conceptual)

| Attribute | Detail |
|---|---|
| **Project** | OTTO -- open-source digital groovebox inspired by OP-1 |
| **Target** | Raspberry Pi 3B+ (not STM32) |
| **Source** | [github.com/bitfieldaudio/OTTO](https://github.com/bitfieldaudio/OTTO) |
| **Status** | Stalled/abandoned (was WIP, never reached production) |

- The OTTO project demonstrates the scope of building a complete groovebox from scratch
- Its design (sampler, sequencer, synth, effects) maps closely to the Blackbox's feature set
- However, it targets Linux/Raspberry Pi, so porting to bare-metal STM32H7 would be a massive undertaking
- More useful as architectural inspiration than portable code

---

### 4.4 Other Relevant Open Source Audio Projects

| Project | Platform | Relevance |
|---|---|---|
| **TOERN** | Teensy 4.1 (Cortex-M7) | Open-source sequencer/sampler/looper on same CPU core family |
| **MicroDexed Touch** | Teensy 4.1 | Multi-engine groovebox with sampler engine |
| **Zynthian** | Raspberry Pi | Full open-source synth platform (Linux-based, different architecture) |
| **PGB-1** | RP2040 | Pocket groovebox with open firmware |

---

## 5. Lessons and Applicability to the Blackbox

### 5.1 The Spectrum of Openness

From the research, music hardware falls on a spectrum:

| Level | Example | Description |
|---|---|---|
| **Fully open source** | Mutable Instruments, Deluge, Axoloti | Full firmware source code released |
| **Firmware binary released for generic hardware** | Dirtywave M8 Headless | Precompiled firmware for DIY hardware |
| **Official plugin SDK** | Korg logue SDK | Sandboxed user code, closed core |
| **Firmware repacking** | TE OP-1 | Community unpacks/modifies/repacks update files |
| **OS-level hacking** | Akai MPC (Linux) | SSH access, identity spoofing, sideloading |
| **Binary analysis only** | Blackbox (current state) | String extraction, memory map analysis from .bin files |
| **Fully locked down** | Elektron Digitakt/Digitone | No known modding community, encrypted firmware |

**The Blackbox currently sits near the bottom of this spectrum.** The firmware is distributed as raw `.bin` files (not encrypted, based on successful string extraction), which places it above fully-locked devices but below anything with active modification.

### 5.2 What Makes Reverse Engineering Feasible

Based on the precedents:

| Factor | Favorable for Blackbox? | Notes |
|---|---|---|
| Firmware distributed as raw binary | **Yes** | `.bin` files on SD card, strings extractable |
| Debug strings left in binary | **Yes** | C++ class names, file paths, developer usernames found |
| Well-known MCU family | **Yes** | STM32H7 is extremely well-documented |
| Standard RTOS | **Yes** | FreeRTOS is open source and well-understood |
| Standard HAL | **Yes** | STM32 HAL is open source |
| Standard filesystem | **Yes** | FatFS is open source |
| Physical debug port (SWD) | **Unknown** | Would need PCB inspection / teardown |
| Read protection level | **Unknown** | Could be RDP Level 0, 1, or 2 |
| Community size | **Small** | Fewer users than MPC/Deluge/OP-1 ecosystems |
| Manufacturer attitude | **Unknown** | 1010music has not commented on open-sourcing |

### 5.3 Key Lessons from Each Project

**From the Deluge:** The manufacturer's cooperation transforms everything. If 1010music chose to open-source the Blackbox firmware (especially as they shift focus to the Bento), the community could deliver real improvements within months. The Patreon model for compensating contributors works.

**From the M8:** Even releasing precompiled firmware for generic hardware (without source code) creates enormous goodwill and community engagement. 1010music could release a "Blackbox Headless" firmware for the Daisy Seed.

**From Mutable Instruments:** Open-source DSP code outlives the company and the hardware. The Blackbox is already CPU-constrained; community optimization of DSP routines could squeeze out more voices/effects.

**From the OP-1:** Firmware repacking is the lowest-effort entry point for community mods. The Blackbox's raw `.bin` format may be amenable to similar analysis -- identifying parameter tables, graphics assets, and configuration data within the binary.

**From the MPC:** Linux-based devices are fundamentally easier targets. The Blackbox's bare-metal FreeRTOS architecture is significantly harder to modify without source code, because there's no shell, no filesystem to modify at runtime, and no standard exploitation surface.

**From Korg logue SDK:** A plugin/SDK approach lets manufacturers maintain control while enabling community creativity. 1010music could expose a "user DSP callback" without opening the entire firmware.

**From Daisy/Axoloti:** Complete open-source audio platforms on STM32 exist and work well. If the Blackbox hardware were documented, a from-scratch alternative firmware built on libDaisy/DaisySP is technically feasible.

### 5.4 Realistic Paths Forward for the Blackbox

In order of feasibility:

1. **Advocate for official open-sourcing** -- Following the Deluge model. Most impactful, but requires 1010music's cooperation. The Bento launch (new hardware generation) could be the trigger, as the Blackbox platform becomes "legacy."

2. **Firmware binary analysis and parameter modding** -- Following the OP-1 model. Build tools to identify and modify parameters, default values, and assets within the `.bin` file. Does not require hardware access.

3. **Hardware teardown and SWD exploration** -- Determine if debug ports are accessible and if RDP is enabled. If RDP is Level 0, full firmware extraction and Ghidra/IDA analysis becomes possible.

4. **Alternative firmware based on Daisy/libDaisy** -- If SWD access is available and RDP allows flashing, build a new firmware from scratch using the open-source Daisy ecosystem. This is a massive effort but technically feasible given the identical MCU family.

5. **Lobby for a plugin SDK** -- Following the Korg logue model. Ask 1010music to expose a user-code sandbox for custom effects or synthesis algorithms, without opening the full firmware.

---

## 6. STM32 Read Protection Considerations

The STM32H7 implements three Read Protection (RDP) levels that determine whether firmware can be extracted via SWD/JTAG:

| RDP Level | Debug Access | Firmware Readable? | Reversible? |
|---|---|---|---|
| **Level 0** | Full | Yes -- direct readout via ST-Link | N/A |
| **Level 1** | Blocked (bus error on flash read) | Not directly; SRAM may be accessible | Yes (but triggers flash erase) |
| **Level 2** | Permanently disabled | No | **Irreversible** |

**Known bypass research:**
- Voltage fault injection (glitching) has been demonstrated against STM32F1 and STM32F4 to bypass RDP Level 1
- The STM32H7 has a different memory architecture and may be more resistant to these attacks
- RDP Level 2 has no known bypass on any STM32 family
- **The Blackbox's RDP level is unknown** and would require physical probing of the SWD pins to determine

**The RDP level is the single biggest unknown** in determining whether the Blackbox firmware can be fully reverse-engineered without manufacturer cooperation.

---

## Sources

### Synthstrom Deluge
- [Synthstrom Open Source Announcement](https://synthstrom.com/open/)
- [Deluge Community Firmware GitHub](https://github.com/SynthstromAudible/DelugeFirmware)
- [Community Firmware 1.0 Release](https://forums.synthstrom.com/discussion/5575/community-firmware-1-0-released)
- [Deluge Community Site](https://delugecommunity.com/)
- [Synthtopia Coverage](https://www.synthtopia.com/content/2023/05/10/synthstrom-deluge-goes-open-source/)
- [CDM Coverage](https://cdm.link/2023/05/synthstrom-deluge-open-source/)

### Dirtywave M8
- [M8 Headless Firmware](https://github.com/Dirtywave/M8HeadlessFirmware)
- [m8c Cross-platform Client](https://github.com/laamaa/m8c)
- [Dirtywave Official](https://dirtywave.com/)

### Electrosmith Daisy
- [Daisy Seed Product Page](https://electro-smith.com/products/daisy-seed)
- [libDaisy GitHub](https://github.com/electro-smith/libDaisy)
- [DaisySP GitHub](https://github.com/electro-smith/DaisySP)
- [DaisyExamples GitHub](https://github.com/electro-smith/DaisyExamples)
- [Hackster.io Coverage](https://www.hackster.io/news/electrosmith-s-daisy-brings-the-stm32-to-bear-on-the-world-of-electronic-music-stem-education-0fa1c2c4269d)

### Mutable Instruments
- [Eurorack Firmware GitHub (pichenettes)](https://github.com/pichenettes/eurorack)
- [Firmware Customization Fork (joeSeggiola)](https://github.com/joeSeggiola/eurorack)
- [Perfect Circuit Retrospective](https://www.perfectcircuit.com/signal/mutable-instruments-retrospective)

### Teenage Engineering OP-1
- [op1repacker GitHub](https://github.com/op1hacks/op1repacker)
- [OP-1 Firmware Archive](https://github.com/op1hacks/op1-fw-archive)
- [op1dumps Hardware Research](https://github.com/Tolsi/op1dumps)
- [OP Forums Custom Firmware Thread](https://op-forums.com/t/custom-firmware-on-the-op-1/4283)
- [Reverse Engineering TE Firmware (wmealing)](https://wmealing.github.io/reverse-engineering-teenage-engineering.html)

### Akai MPC
- [MPC-LiveXplore (TheKikGen)](https://github.com/TheKikGen/MPC-LiveXplore)
- [Hakai Custom Firmware](https://github.com/henning/Hakai-MPC)
- [MockbaMod (Force)](https://github.com/MockbaTheBorg/MockbaMod)
- [MPC Live Internals (Niklas Nisbeth)](https://niklasnisbeth.gitlab.io/mpc-internals/)
- [Synthtopia Hakai Coverage](https://www.synthtopia.com/content/2023/05/22/unofficial-mpc-hack-hakai-lets-you-run-force-firmware/)

### Korg logue SDK
- [logue-sdk GitHub](https://github.com/korginc/logue-sdk)
- [NTS-1 Customizations](https://korginc.github.io/nts-1-customizations/)

### Roland AIRA
- [AIRA Modular Effects RE (mugenkidou)](https://github.com/mugenkidou/AIRA_Modular_Effects)
- [AIRA Modular Customizer](https://www.roland.com/global/products/aira_modular_customizer/)

### Axoloti
- [Axoloti GitHub](https://github.com/axoloti/axoloti)
- [Ksoloti Community Continuation](https://www.modwiggler.com/forum/viewtopic.php?t=277847)

### OTTO
- [OTTO GitHub](https://github.com/bitfieldaudio/OTTO)

### STM32 Security Research
- [STM32 RDP Levels (stm32world.com)](https://stm32world.com/wiki/STM32_Readout_Protection_(RDP))
- [Voltage Glitching STM32F4 (jerinsunny)](https://jerinsunny.github.io/stm32_vglitch/)
- [Glitching STM32 RDP (Anvil Secure)](https://www.anvilsecure.com/blog/glitching-stm32-read-out-protection-with-voltage-fault-injection.html)
- [SWD/JTAG Firmware Extraction (HardBreak)](https://www.hardbreak.wiki/hardware-hacking/interface-interaction/jtag-swd/extract-firmware-using-jtag-swd)
- [SWD Xbox Controller RE (Wrongbaud)](https://wrongbaud.github.io/posts/stm-xbox-jtag/)
- [STM32 Flash Hacking (Hackaday)](https://hackaday.com/2020/03/24/breaking-into-a-secure-facility-stm32-flash/)

### Polyend Tracker
- [Community Firmware Request Thread](https://backstage.polyend.com/t/community-firmware-for-the-polyend-tracker/13778)
- [Open Source Discussion](https://backstage.polyend.com/t/open-source-community-firmware/7008)

### Open Source Groovebox Projects
- [TOERN](https://toern.live/)
- [Zynthian](https://zynthian.org/)
- [Open Source Music Hardware Wiki](https://sdiy.info/wiki/Open_source_music_hardware_projects)
