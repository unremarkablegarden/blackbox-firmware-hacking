# 1010music Blackbox — Hardware & Firmware Deep Dive

## Executive Summary

The Blackbox runs **C++ firmware** on an **STM32H7xx (ARM Cortex-M7)** microcontroller, likely with **FreeRTOS** as the RTOS layer. This was confirmed by direct analysis of the firmware `.bin` files. The internal project is codenamed **"BoomboxFramework"**.

---

## Processor / SoC

| Spec | Detail |
|---|---|
| **MCU** | **STM32H7xx** (likely STM32H743 or STM32H750) |
| **Core** | ARM Cortex-M7 |
| **Clock** | Up to 480 MHz |
| **Evidence** | Firmware binary analysis: initial stack pointer at `0x240609B0` maps to STM32H7 AXI SRAM (region `0x24000000`), reset vector at `0x08040515` maps to STM32 flash. STM32 HAL callbacks (`HAL_ADC_ErrorCallback`, `HAL_SD_ErrorCallback`) found in binary. |

**Note:** Some community forums speculated this was a Microchip SAMA5D4 (Cortex-A5) running Linux. The firmware binary analysis **definitively rules this out** — the memory map and HAL signatures are unmistakably STM32H7.

---

## Memory & Storage

| Component | Detail |
|---|---|
| **External RAM** | **64 MB** (2 x 256 Mbit DDR/SDRAM), confirmed by 1010music on their forum |
| **On-chip SRAM** | ~1 MB (STM32H7 internal — AXI SRAM, DTCM, ITCM, etc.) |
| **Storage** | MicroSD card (FAT32, user-supplied) — samples stream directly from card |
| **Firmware flash** | Internal flash with ~256 KB bootloader region |

---

## Firmware / Software Stack

| Layer | Technology |
|---|---|
| **Language** | **C++** (with C for HAL/USB layers) |
| **RTOS** | **FreeRTOS** (evidenced by `defaultTask`, `audioTask`, `pcmStreamer` task names — typical of STM32CubeMX/FreeRTOS generation) |
| **HAL** | STM32 HAL (ST's Hardware Abstraction Layer) |
| **Filesystem** | **FatFS** (standard STM32Cube filesystem for SD cards) |
| **USB** | STM32 USB Host library |
| **Dev platform** | Windows (`C:\Projects\Code\matrixsw\BoomboxFramework\Src\...`) |
| **Internal codename** | **"BoomboxFramework"** under org **"matrixsw"** |
| **Source status** | Proprietary, closed-source |

**Not Linux** — despite community speculation, the binary structure (vector table, HAL callbacks, FreeRTOS tasks, Cortex-M7 memory map) confirms this is a bare-metal/RTOS firmware, not a Linux system.

### Key C++ Classes Found in Firmware Binary

Extracted from symbol/string analysis of the `.bin` files:

- `PowerMgr::Shutdown`, `PowerMgr::SetLowPowerMode`
- `SessionMgr::LoadBank`, `SessionMgr::FinalizeBankLoading`
- `PresetMgr::RequestPresetLoad`, `PresetMgr::SaveAs`, `PresetMgr::PackPreset`
- `UIToolbar::InsertButton`
- `WaveFileFF::WriteHeader`, `WaveFileFF::OpenWriteFile`, `WaveFileFF::PushData`
- `BlamSliceVoice::StartNote`, `BlamSliceVoice::ProcessNote`
- `BlamMVoicePool::GetVoice`
- `BitmapFile::SaveToFile`

### Source Files Embedded in Binary

Paths left in debug info:

```
C:\Projects\Code\matrixsw\BoomboxFramework\Src\usbh_conf.c
C:\Projects\Code\matrixsw\BoomboxFramework\Src\I2CPortBoombox.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\AnalogInput.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\AudioDriverBoombox.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\SDMgr.cpp
C:\Projects\Code\matrixsw\BoomboxFramework\Src\MidiPort.cpp
```

The v2.0E firmware also reveals a developer's Windows username: `C:\Users\kf6gp\Projects\Code\...`

---

## Key People

| Person | Role |
|---|---|
| **Aaron Higgins** | Founder & principal engineer. Ex-Microsoft audio evangelist (1997-2000), creator of MixMeister, iOS app Looptastic (team acquired by Native Instruments for Traktor DJ). Built the custom OS from scratch. |
| **Christine Higgins** | Co-founder, Senior Business Analyst. Handles ops and hiring. |
| **Ray Rischpater** (KF6GPE) | Firmware developer. His Windows username `kf6gp` appears in the v2.0E firmware binary. His website states he works on "firmware for synthesizers and samplers on bespoke ARM systems" at 1010music. 30+ years embedded experience, ex-Nokia/Microsoft/Uber/Google. |

---

## Audio & I/O

| Component | Detail |
|---|---|
| **Audio codec** | Dedicated codec IC (exact part undisclosed — likely Cirrus Logic CS42xx or TI TLV320AIC family) |
| **Audio spec** | 24-bit, 44.1/48 kHz, stereo in + stereo out + headphone out |
| **Display** | 3.5" color TFT LCD touchscreen, 480x320 |
| **MIDI** | 3.5mm TRS Type-A, In + Out |
| **USB** | Micro-USB (power, USB-MIDI, firmware update) |
| **Power** | 5V via USB (can run from battery pack) |

---

## Platform Sharing

1010music reuses the same core hardware across products — the differentiator is firmware:

| Product | Form Factor | Same Platform? |
|---|---|---|
| **Bitbox** / **Fxbox** / **Synthbox** | Eurorack (Series 1) | Identical boards, swappable firmware |
| **Toolbox** / **Laserbox** | Eurorack (Series 2) | Different board from Series 1 |
| **Blackbox** | Desktop sampler | Shared platform |
| **Bluebox** | Desktop mixer | Shared platform |
| **Bitbox MK2** | Eurorack | "Slightly better" processor, same RAM (64 MB) |
| **Nanobox line** | Tiny desktop | Shared among Lemondrop/Fireball/Razzmatazz/Tangerine |
| **Bento** (2025) | Portable studio | **Completely new OS rewrite**, new hardware generation |

---

## Why STM32H7?

The Cortex-M7 is a pragmatic choice for a dedicated audio appliance:

- **Deterministic, hard real-time** — no OS jitter, critical for low-latency audio
- **Hardware DSP** — FPU + DSP instructions on Cortex-M7 for audio processing
- **Low power** — no fan, runs cool, USB-powered
- **Rich peripherals** — I2S/SAI for audio, SDMMC, LCD controller, USB OTG
- **Cost-effective** — much cheaper than application processors

The tradeoff is limited CPU headroom: the Blackbox maxes out at ~24-32 voices, and granular processing at 8 grains "eats up the processor."

---

## Sources

- 1010music forum: "What's under the hood?" thread — official confirmation of C++, 64 MB RAM, codec details
- Firmware binary analysis of files in `Firmwares/` directory (v1.02, v2.0E, v3.12)
- Ray Rischpater's personal website (lothlorien.com/kf6gpe/about/)
- DJ.Studio interview with Aaron Higgins
- Art + Music + Technology Podcast #272 (April 2019)
- Sound on Sound reviews (Blackbox, Bento)
- ModWiggler, Gearspace, and Elektronauts forum threads
- Christine Higgins LinkedIn (C++ developer hiring post)
- 1010music firmware swapping documentation (1010music.com/support/firmware-swapping)

---

*The firmest findings (STM32H7, C++, FreeRTOS, BoomboxFramework) come from direct binary analysis of the firmware files. The audio codec part number remains the biggest unknown — that would require a physical teardown to read chip markings.*
