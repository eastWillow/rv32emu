/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
#include "tx_port.h"

.section .text.boot, "ax"
.global _start
_start:
    csrci mstatus, 8
    csrw mie, zero
    .option push
    .option norelax
    la gp, __global_pointer$
    .option pop
    la sp, _stack_top
    la t0, _bss_start
    la t1, _bss_end
1:
    bgeu t0, t1, 2f
    sw zero, 0(t0)
    addi t0, t0, 4
    j 1b
2:
    call main
3:
    wfi
    j 3b

.section .text
.balign 4
.global _tx_initialize_low_level
_tx_initialize_low_level:
    la t0, _tx_thread_system_stack_ptr
    sw sp, 0(t0)
    la t0, _tx_initialize_unused_memory
    la t1, _end
    sw t1, 0(t0)
    la t0, trap_entry
    csrw mtvec, t0
    /* ThreadX enables MIE when its scheduler restores the first thread. */
    li t0, 0x1880
    csrs mstatus, t0
    li t0, 0x80
    csrw mie, t0
    addi sp, sp, -16
    sw ra, 0(sp)
    call board_init
    lw ra, 0(sp)
    addi sp, sp, 16
    ret

.balign 4
trap_entry:
    /* The upstream port's integer interrupt frame and RA slot. */
    addi sp, sp, -TX_RISCV_TRAP_FRAME_SIZE
    sw ra, 112(sp)
    call _tx_thread_context_save
    csrr a0, mcause
    csrr a1, mepc
    csrr a2, mtval
    call board_trap
    j _tx_thread_context_restore
