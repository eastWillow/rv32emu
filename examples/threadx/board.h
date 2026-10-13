/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
#pragma once
#include <stdint.h>
void board_init(void);
void board_trap(uint32_t cause, uint32_t pc, uint32_t value);
void board_puts(const char *text);
_Noreturn void board_exit(unsigned code);

/* Timer entry supplied by the upstream ThreadX assembly port. */
void _tx_timer_interrupt(void);
