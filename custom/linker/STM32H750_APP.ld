/*
 * Linker script for Blackbox custom firmware
 * STM32H750 / STM32H743 — Application region only
 *
 * The bootloader occupies 0x08000000 - 0x0803FFFF (256KB)
 * Our application loads at 0x08040000 (matching stock firmware)
 */

MEMORY
{
    /* Application flash — after bootloader */
    FLASH (rx)      : ORIGIN = 0x08040000, LENGTH = 1792K   /* 2MB - 256KB bootloader */

    /* Tightly coupled memory — fastest access */
    DTCM (rwx)      : ORIGIN = 0x20000000, LENGTH = 128K
    ITCM (rwx)      : ORIGIN = 0x00000000, LENGTH = 64K

    /* AXI SRAM — main RAM, used by stock firmware for stack + heap */
    AXI_SRAM (rwx)  : ORIGIN = 0x24000000, LENGTH = 512K

    /* D2 domain SRAM — good for DMA buffers */
    SRAM1 (rwx)     : ORIGIN = 0x30000000, LENGTH = 128K
    SRAM2 (rwx)     : ORIGIN = 0x30020000, LENGTH = 128K
    SRAM3 (rwx)     : ORIGIN = 0x30040000, LENGTH = 32K

    /* D3 domain SRAM — accessible in low-power modes */
    SRAM4 (rwx)     : ORIGIN = 0x38000000, LENGTH = 64K
}

/* Initial stack pointer — top of AXI SRAM (matching stock firmware) */
_estack = ORIGIN(AXI_SRAM) + LENGTH(AXI_SRAM);

/* Heap configuration */
_Min_Heap_Size  = 0x10000;  /* 64KB minimum heap */
_Min_Stack_Size = 0x2000;   /* 8KB minimum stack */

ENTRY(Reset_Handler)

SECTIONS
{
    /* Vector table must be first */
    .isr_vector :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector))
        . = ALIGN(4);
    } >FLASH

    /* Code */
    .text :
    {
        . = ALIGN(4);
        *(.text)
        *(.text*)
        *(.glue_7)
        *(.glue_7t)
        *(.eh_frame)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        _etext = .;
    } >FLASH

    /* Read-only data */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } >FLASH

    /* ARM exception handling */
    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } >FLASH

    .ARM :
    {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } >FLASH

    /* C++ constructors */
    .preinit_array :
    {
        PROVIDE_HIDDEN(__preinit_array_start = .);
        KEEP(*(.preinit_array*))
        PROVIDE_HIDDEN(__preinit_array_end = .);
    } >FLASH

    .init_array :
    {
        PROVIDE_HIDDEN(__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array*))
        PROVIDE_HIDDEN(__init_array_end = .);
    } >FLASH

    .fini_array :
    {
        PROVIDE_HIDDEN(__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array*))
        PROVIDE_HIDDEN(__fini_array_end = .);
    } >FLASH

    /* Initialized data — stored in flash, copied to RAM at startup */
    _sidata = LOADADDR(.data);
    .data :
    {
        . = ALIGN(4);
        _sdata = .;
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } >AXI_SRAM AT> FLASH

    /* Zero-initialized data */
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
        __bss_end__ = _ebss;
    } >AXI_SRAM

    /* Heap — grows up from end of BSS */
    ._user_heap :
    {
        . = ALIGN(8);
        PROVIDE(end = .);
        PROVIDE(_end = .);
        . = . + _Min_Heap_Size;
        . = ALIGN(8);
    } >AXI_SRAM

    /* Stack — grows down from top of AXI SRAM */
    ._user_stack :
    {
        . = ALIGN(8);
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
    } >AXI_SRAM

    /* DMA buffers — place in D2 SRAM for DMA access */
    .dma_buffers (NOLOAD) :
    {
        . = ALIGN(32);  /* Cache line aligned */
        *(.dma_buffers)
        *(.dma_buffers*)
        . = ALIGN(32);
    } >SRAM1

    /* Audio buffers — place in DTCM for fastest access */
    .audio_buffers (NOLOAD) :
    {
        . = ALIGN(4);
        *(.audio_buffers)
        *(.audio_buffers*)
        . = ALIGN(4);
    } >DTCM

    /DISCARD/ :
    {
        libc.a(*)
        libm.a(*)
        libgcc.a(*)
    }
}
