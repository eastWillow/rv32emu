/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */

/* Freestanding ThreadX only needs memset; no target libc is required. */
#ifndef RV32EMU_THREADX_STRING_H
#define RV32EMU_THREADX_STRING_H
#include <stddef.h>
void *memset(void *dest, int value, size_t size);
#endif
