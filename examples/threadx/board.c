/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
#include "board.h"
#include <stddef.h>
#include <string.h>

#define MTIMECMP ((volatile uint32_t *) 0xF4204000)
#define MTIME ((volatile uint32_t *) 0xF420BFF8)
#define UART ((volatile uint8_t *) 0xF4000000)
#define FINISHER (*(volatile uint32_t *) 0xF4300000)
#define TICK_CYCLES 1000

void *memset(void *dest, int value, size_t size)
{
    unsigned char *p = dest;
    while (size--)
        *p++ = (unsigned char) value;
    return dest;
}

static uint64_t timer_now(void)
{
    uint32_t hi, lo;
    do {
        hi = MTIME[1];
        lo = MTIME[0];
    } while (hi != MTIME[1]);
    return ((uint64_t) hi << 32) | lo;
}

static void timer_arm(void)
{
    uint64_t next = timer_now() + TICK_CYCLES;
    /* RV32 safe sequence: avoid transiently programming a past compare. */
    MTIMECMP[0] = UINT32_MAX;
    MTIMECMP[1] = next >> 32;
    MTIMECMP[0] = next;
}

void board_init(void)
{
    timer_arm();
}

void board_puts(const char *text)
{
    while (*text) {
        while (!(UART[5] & 0x20))
            ;
        UART[0] = *text++;
    }
}

_Noreturn void board_exit(unsigned code)
{
    __asm__ volatile("csrci mstatus, 8" ::: "memory");
    FINISHER = code ? (code << 16) | 0x3333 : 0x5555;
    for (;;)
        __asm__ volatile("wfi");
}

void board_trap(uint32_t cause, uint32_t pc, uint32_t value)
{
    (void) pc;
    (void) value;
    if (cause != 0x80000007) {
        board_puts("ThreadX trap FAIL\n");
        board_exit(1);
    }
    timer_arm();
    _tx_timer_interrupt();
}
