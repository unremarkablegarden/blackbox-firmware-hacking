/**
 * Blackbox Custom Firmware — Minimal Main
 *
 * This is a skeleton that boots on the Blackbox hardware.
 * It initializes the system clock and blinks... something.
 *
 * TODO: Once pin mappings are extracted from firmware disassembly:
 * - Initialize the display (SPI or LTDC)
 * - Initialize the audio codec (SAI/I2S)
 * - Initialize SD card (SDMMC)
 * - Initialize USB (OTG)
 * - Initialize MIDI (UART)
 */

#include <stdint.h>

/* STM32H7 register definitions — minimal subset */
#define RCC_BASE        0x58024400UL
#define RCC_AHB4ENR     (*(volatile uint32_t *)(0x580244E0UL))  /* GPIO clocks */
#define RCC_CR          (*(volatile uint32_t *)(0x58024400UL))
#define RCC_CFGR        (*(volatile uint32_t *)(0x58024410UL))

/* GPIO base addresses */
#define GPIOA_BASE      0x58020000UL
#define GPIOB_BASE      0x58020400UL
#define GPIOC_BASE      0x58020800UL
#define GPIOD_BASE      0x58020C00UL
#define GPIOE_BASE      0x58021000UL

/* GPIO register offsets */
#define GPIO_MODER      0x00
#define GPIO_OTYPER     0x04
#define GPIO_OSPEEDR    0x08
#define GPIO_PUPDR      0x0C
#define GPIO_IDR        0x10
#define GPIO_ODR        0x14
#define GPIO_BSRR       0x18

#define GPIO_REG(base, offset)  (*(volatile uint32_t *)((base) + (offset)))

/* System tick */
#define SYSTICK_CSR     (*(volatile uint32_t *)0xE000E010UL)
#define SYSTICK_RVR     (*(volatile uint32_t *)0xE000E014UL)
#define SYSTICK_CVR     (*(volatile uint32_t *)0xE000E018UL)

volatile uint32_t systick_ms = 0;

void SysTick_Handler(void) {
    systick_ms++;
}

static void delay_ms(uint32_t ms) {
    uint32_t start = systick_ms;
    while ((systick_ms - start) < ms) {
        __asm volatile("wfi");  /* Wait for interrupt — saves power */
    }
}

static void systick_init(uint32_t cpu_freq_hz) {
    /* Configure SysTick for 1ms interrupts */
    SYSTICK_RVR = (cpu_freq_hz / 1000) - 1;
    SYSTICK_CVR = 0;
    SYSTICK_CSR = 0x07;  /* Enable, interrupt, use processor clock */
}

/**
 * Main entry point
 *
 * At this stage we're running on the HSI oscillator (64 MHz).
 * The full clock tree setup (PLL for 480 MHz, SAI clocks for audio)
 * requires knowing the exact crystal frequency and PLL configuration,
 * which can be extracted from the stock firmware disassembly.
 */
int main(void) {
    /* Enable GPIO clocks (all ports) */
    RCC_AHB4ENR |= 0x7FF;  /* GPIOA through GPIOK */

    /* Small delay for clocks to stabilize */
    for (volatile int i = 0; i < 100000; i++);

    /* Set up SysTick at 64 MHz (HSI default) */
    systick_init(64000000);

    /*
     * ================================================================
     * YOUR CODE HERE
     *
     * Next steps (extract pin mappings from Ghidra first):
     *
     * 1. display_init()  — Initialize the 3.5" TFT LCD
     * 2. sdcard_init()   — Mount the SD card via SDMMC + FatFS
     * 3. codec_init()    — Configure the audio codec via I2C + SAI
     * 4. usb_init()      — USB MIDI host/device
     * 5. midi_init()     — UART-based TRS MIDI
     *
     * For now, we just prove we're alive by toggling GPIOs.
     * Connect an LED or oscilloscope to any GPIO to verify.
     * ================================================================
     */

    /* Example: Toggle PA0 as a heartbeat (may or may not be connected to anything) */
    GPIO_REG(GPIOA_BASE, GPIO_MODER) &= ~(0x3 << (0 * 2));  /* Clear mode bits */
    GPIO_REG(GPIOA_BASE, GPIO_MODER) |=  (0x1 << (0 * 2));   /* Output mode */

    while (1) {
        GPIO_REG(GPIOA_BASE, GPIO_BSRR) = (1 << 0);      /* Set PA0 */
        delay_ms(500);
        GPIO_REG(GPIOA_BASE, GPIO_BSRR) = (1 << 16);     /* Reset PA0 */
        delay_ms(500);
    }

    return 0;
}
