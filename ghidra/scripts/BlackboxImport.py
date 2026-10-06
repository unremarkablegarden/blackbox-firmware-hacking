# Ghidra headless analysis script for Blackbox firmware
# Run via: analyzeHeadless <project_dir> BlackboxProject -import <firmware.bin> -postScript BlackboxImport.py
#
# Or manually in Ghidra GUI:
#   1. Import firmware.bin with Language "ARM:LE:32:Cortex"
#   2. Set base address to 0x08040000
#   3. Run this script via Script Manager

# @category Blackbox
# @author blackbox-re

import struct

APP_BASE = 0x08040000

# STM32H7 memory regions to add
MEMORY_REGIONS = [
    ("DTCM_RAM",  0x20000000, 0x20000, True),   # 128KB
    ("AXI_SRAM",  0x24000000, 0x80000, True),   # 512KB
    ("SRAM1",     0x30000000, 0x20000, True),   # 128KB
    ("SRAM2",     0x30020000, 0x20000, True),   # 128KB
    ("SRAM3",     0x30040000, 0x08000, True),   # 32KB
    ("SRAM4",     0x38000000, 0x10000, True),   # 64KB
]

# Key STM32H7 peripheral base addresses
PERIPHERAL_LABELS = {
    0x40000000: "TIM2",
    0x40000400: "TIM3",
    0x40000800: "TIM4",
    0x40000C00: "TIM5",
    0x40001000: "TIM6",
    0x40001400: "TIM7",
    0x40001800: "TIM12",
    0x40001C00: "TIM13",
    0x40002000: "TIM14",
    0x40003800: "SPI2_I2S2",
    0x40003C00: "SPI3_I2S3",
    0x40004400: "USART2",
    0x40004800: "USART3",
    0x40004C00: "UART4",
    0x40005000: "UART5",
    0x40005400: "I2C1",
    0x40005800: "I2C2",
    0x40005C00: "I2C3",
    0x40007800: "DAC1",
    0x40008400: "UART7",
    0x40008800: "UART8",
    0x40010000: "TIM1",
    0x40010400: "TIM8",
    0x40011000: "USART1",
    0x40011400: "USART6",
    0x40013000: "SPI1_I2S1",
    0x40013400: "SPI4",
    0x40013800: "TIM15",
    0x40013C00: "TIM16",
    0x40014000: "TIM17",
    0x40015000: "SPI5",
    0x40015800: "SAI1",
    0x40015C00: "SAI2",
    0x40016000: "SAI3",
    0x40020000: "GPIOA",
    0x40020400: "GPIOB",
    0x40020800: "GPIOC",
    0x40020C00: "GPIOD",
    0x40021000: "GPIOE",
    0x40021400: "GPIOF",
    0x40021800: "GPIOG",
    0x40021C00: "GPIOH",
    0x40022000: "GPIOI",
    0x40022400: "GPIOJ",
    0x40022800: "GPIOK",
    0x40023000: "RCC",
    0x40023800: "FLASH_REG",
    0x40023C00: "CRC",
    0x40026400: "DMA1",
    0x40026800: "DMA2",
    0x40028000: "DMAMUX1",
    0x40040000: "ADC1",
    0x40040100: "ADC2",
    0x40040300: "ADC_Common",
    0x48021000: "SDMMC2",
    0x48022800: "MDMA",
    0x50001000: "QUADSPI",
    0x52007000: "SDMMC1",
    0x58024400: "EXTI",
    0x58024800: "SYSCFG",
    0x58025400: "SAI4",
    0x58026000: "IWDG1",
    0x5C001000: "PWR",
    0x40080000: "OTG_HS",
    0x40040000: "OTG_FS",
}

# Cortex-M exception names
EXCEPTION_NAMES = [
    "ISR_InitialSP", "ISR_Reset", "ISR_NMI", "ISR_HardFault",
    "ISR_MemManage", "ISR_BusFault", "ISR_UsageFault",
    None, None, None, None,
    "ISR_SVCall", "ISR_DebugMon", None, "ISR_PendSV", "ISR_SysTick",
]

STM32H7_IRQ_NAMES = {
    0: "ISR_WWDG", 1: "ISR_PVD", 4: "ISR_FLASH", 5: "ISR_RCC",
    11: "ISR_DMA1_Stream0", 12: "ISR_DMA1_Stream1", 13: "ISR_DMA1_Stream2",
    14: "ISR_DMA1_Stream3", 15: "ISR_DMA1_Stream4", 16: "ISR_DMA1_Stream5",
    17: "ISR_DMA1_Stream6", 18: "ISR_ADC", 31: "ISR_I2C1_EV",
    32: "ISR_I2C1_ER", 33: "ISR_I2C2_EV", 34: "ISR_I2C2_ER",
    35: "ISR_SPI1", 36: "ISR_SPI2", 37: "ISR_USART1", 38: "ISR_USART2",
    47: "ISR_DMA1_Stream7", 48: "ISR_FMC", 49: "ISR_SDMMC1",
    50: "ISR_TIM5", 51: "ISR_SPI3", 54: "ISR_TIM6_DAC",
    56: "ISR_DMA2_Stream0", 57: "ISR_DMA2_Stream1", 58: "ISR_DMA2_Stream2",
    59: "ISR_DMA2_Stream3", 60: "ISR_DMA2_Stream4",
    67: "ISR_DMA2_Stream5", 68: "ISR_DMA2_Stream6", 69: "ISR_DMA2_Stream7",
    73: "ISR_OTG_HS_EP1_OUT", 74: "ISR_OTG_HS_EP1_IN", 76: "ISR_OTG_HS",
    82: "ISR_UART7", 83: "ISR_UART8", 87: "ISR_SAI1", 88: "ISR_LTDC",
    90: "ISR_DMA2D", 91: "ISR_SAI2", 92: "ISR_QUADSPI",
    95: "ISR_SDMMC2", 110: "ISR_MDMA", 124: "ISR_SAI4",
}


def run():
    from ghidra.program.model.symbol import SourceType
    from ghidra.program.model.mem import MemoryBlockType
    from ghidra.app.util.importer import MessageLog

    memory = currentProgram.getMemory()
    listing = currentProgram.getListing()
    symTable = currentProgram.getSymbolTable()
    addrFactory = currentProgram.getAddressFactory()
    space = addrFactory.getDefaultAddressSpace()

    def addr(offset):
        return space.getAddress(offset)

    # --- Add RAM regions ---
    println("Adding STM32H7 memory regions...")
    for name, start, size, is_volatile in MEMORY_REGIONS:
        try:
            block = memory.createUninitializedBlock(name, addr(start), size, False)
            block.setRead(True)
            block.setWrite(True)
            block.setExecute(False)
            block.setVolatile(is_volatile)
            println("  Added: %s at 0x%08X (%d KB)" % (name, start, size // 1024))
        except Exception as e:
            println("  Skip %s: %s" % (name, str(e)))

    # --- Label vector table entries ---
    println("\nLabeling vector table...")
    block = memory.getBlock(addr(APP_BASE))
    if block is not None:
        for i in range(160):
            vec_addr = APP_BASE + i * 4
            try:
                val = memory.getInt(addr(vec_addr))
            except:
                break

            handler_addr = val & 0xFFFFFFFE  # Clear Thumb bit

            # Determine name
            name = None
            if i < len(EXCEPTION_NAMES):
                name = EXCEPTION_NAMES[i]
            elif (i - 16) in STM32H7_IRQ_NAMES:
                name = STM32H7_IRQ_NAMES[i - 16]

            if name and val != 0 and i > 0:
                try:
                    symTable.createLabel(addr(handler_addr), name, SourceType.ANALYSIS)
                    createFunction(addr(handler_addr), name)
                    println("  %s -> 0x%08X" % (name, handler_addr))
                except:
                    pass

    # --- Label peripheral addresses ---
    println("\nLabeling peripheral registers...")
    for periph_addr, name in PERIPHERAL_LABELS.items():
        try:
            symTable.createLabel(addr(periph_addr), name + "_BASE", SourceType.ANALYSIS)
        except:
            pass

    println("\nBlackbox import script complete!")
    println("Next steps:")
    println("  1. Run Auto Analysis (Analysis -> Auto Analyze)")
    println("  2. Load SVD file via SVD-Loader plugin for detailed peripheral register names")
    println("  3. Look for xTaskCreate calls to find RTOS task entry points")
    println("  4. Search strings for '::' to find C++ methods")


run()
