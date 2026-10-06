/**
 * Minimal startup code for STM32H750/H743
 * Sets up vector table, copies .data, zeros .bss, calls main()
 *
 * This is the bare minimum to boot on the Blackbox hardware.
 * The vector table layout matches what the stock bootloader expects.
 */

  .syntax unified
  .cpu cortex-m7
  .fpu fpv5-d16
  .thumb

/* Vector table — must be at the start of flash (0x08040000 for app) */
  .section .isr_vector, "a", %progbits
  .type g_pfnVectors, %object
  .size g_pfnVectors, .-g_pfnVectors

g_pfnVectors:
  .word _estack                  /* Initial stack pointer */
  .word Reset_Handler            /* Reset */
  .word NMI_Handler              /* NMI */
  .word HardFault_Handler        /* Hard Fault */
  .word MemManage_Handler        /* MPU Fault */
  .word BusFault_Handler         /* Bus Fault */
  .word UsageFault_Handler       /* Usage Fault */
  .word 0                        /* Reserved */
  .word 0                        /* Reserved */
  .word 0                        /* Reserved */
  .word 0                        /* Reserved */
  .word SVC_Handler              /* SVCall */
  .word DebugMon_Handler         /* Debug Monitor */
  .word 0                        /* Reserved */
  .word PendSV_Handler           /* PendSV */
  .word SysTick_Handler          /* SysTick */

  /* STM32H7 IRQs — add handlers as needed */
  .word Default_Handler          /* IRQ0:  WWDG */
  .word Default_Handler          /* IRQ1:  PVD_AVD */
  .word Default_Handler          /* IRQ2:  TAMP_STAMP */
  .word Default_Handler          /* IRQ3:  RTC_WKUP */
  .word Default_Handler          /* IRQ4:  FLASH */
  .word Default_Handler          /* IRQ5:  RCC */
  .word Default_Handler          /* IRQ6:  EXTI0 */
  .word Default_Handler          /* IRQ7:  EXTI1 */
  .word Default_Handler          /* IRQ8:  EXTI2 */
  .word Default_Handler          /* IRQ9:  EXTI3 */
  .word Default_Handler          /* IRQ10: EXTI4 */
  .word Default_Handler          /* IRQ11: DMA1_Stream0 */
  .word Default_Handler          /* IRQ12: DMA1_Stream1 */
  .word Default_Handler          /* IRQ13: DMA1_Stream2 */
  .word Default_Handler          /* IRQ14: DMA1_Stream3 */
  .word Default_Handler          /* IRQ15: DMA1_Stream4 */
  .word Default_Handler          /* IRQ16: DMA1_Stream5 */
  .word Default_Handler          /* IRQ17: DMA1_Stream6 */
  .word Default_Handler          /* IRQ18: ADC */
  .word Default_Handler          /* IRQ19-86: ... (extend as needed) */
  /* Fill remaining vectors with Default_Handler up to IRQ86 (SAI1) */
  .rept 68
  .word Default_Handler
  .endr

/* Reset handler — entry point */
  .section .text.Reset_Handler
  .weak Reset_Handler
  .type Reset_Handler, %function
Reset_Handler:
  /* Set stack pointer (redundant but safe) */
  ldr sp, =_estack

  /* Enable FPU (CP10 + CP11 full access) */
  ldr r0, =0xE000ED88
  ldr r1, [r0]
  orr r1, r1, #(0xF << 20)
  str r1, [r0]
  dsb
  isb

  /* Copy .data from flash to RAM */
  ldr r0, =_sdata
  ldr r1, =_edata
  ldr r2, =_sidata
  movs r3, #0
  b .Ldata_check
.Ldata_copy:
  ldr r4, [r2, r3]
  str r4, [r0, r3]
  adds r3, r3, #4
.Ldata_check:
  adds r4, r0, r3
  cmp r4, r1
  bcc .Ldata_copy

  /* Zero .bss */
  ldr r0, =_sbss
  ldr r1, =_ebss
  movs r2, #0
  b .Lbss_check
.Lbss_zero:
  str r2, [r0]
  adds r0, r0, #4
.Lbss_check:
  cmp r0, r1
  bcc .Lbss_zero

  /* Call C++ static constructors */
  bl __libc_init_array

  /* Jump to main */
  bl main

  /* If main returns, loop forever */
  b .

  .size Reset_Handler, .-Reset_Handler

/* Default handlers — infinite loops (override with your own) */
  .section .text.Default_Handler, "ax", %progbits
Default_Handler:
  b Default_Handler
  .size Default_Handler, .-Default_Handler

  .weak NMI_Handler
  .thumb_set NMI_Handler, Default_Handler

  .weak HardFault_Handler
  .thumb_set HardFault_Handler, Default_Handler

  .weak MemManage_Handler
  .thumb_set MemManage_Handler, Default_Handler

  .weak BusFault_Handler
  .thumb_set BusFault_Handler, Default_Handler

  .weak UsageFault_Handler
  .thumb_set UsageFault_Handler, Default_Handler

  .weak SVC_Handler
  .thumb_set SVC_Handler, Default_Handler

  .weak DebugMon_Handler
  .thumb_set DebugMon_Handler, Default_Handler

  .weak PendSV_Handler
  .thumb_set PendSV_Handler, Default_Handler

  .weak SysTick_Handler
  .thumb_set SysTick_Handler, Default_Handler
