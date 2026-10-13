/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
/* Check machine trap entry, both MPIE values on mret, vectored interrupts,
 * direct exception dispatch through a vectored mtvec, and timer masking.
 */
.section .text
.global _start
_start:
    li s0, 0
    li s1, 0
    li s2, 0xF4204000
    la t0, disabled
    csrw mepc, t0
    li t0, 0x1808
    csrw mstatus, t0
    mret
disabled:
    csrr t0, mstatus
    andi t1, t0, 8
    bnez t1, fail
    andi t1, t0, 0x80
    beqz t1, fail
    la t0, enabled
    csrw mepc, t0
    li t0, 0x1880
    csrw mstatus, t0
    mret
enabled:
    csrr t0, mstatus
    andi t1, t0, 8
    beqz t1, fail
    csrci mstatus, 8
    la t0, vectors
    ori t0, t0, 1
    csrw mtvec, t0
    li t0, 0x80
    csrw mie, t0
    li t0, -1
    sw t0, 0(s2)
    sw zero, 4(s2)
    sw zero, 0(s2)
    csrr t0, mip
    andi t0, t0, 0x80
    beqz t0, fail
    /* MTIP is pending but global MIE is clear. */
ecall_point:
    ecall
    li t0, 1
    bne s0, t0, fail
    bnez s1, fail
    csrsi mstatus, 8
wait_timer:
    beqz s1, wait_timer
    csrr t0, mip
    andi t0, t0, 0x80
    bnez t0, fail
    li t0, 0xF4300000
    li t1, 0x5555
    sw t1, 0(t0)
1:
    j 1b
.balign 4
vectors:
    j exception
    j fail
    j fail
    j fail
    j fail
    j fail
    j fail
    j timer
exception:
    csrr t0, mcause
    li t1, 11
    bne t0, t1, fail
    csrr t0, mepc
    la t1, ecall_point
    bne t0, t1, fail
    csrr t1, mstatus
    andi t1, t1, 0x88
    bnez t1, fail
    addi t0, t0, 4
    csrw mepc, t0
    addi s0, s0, 1
    mret
timer:
    csrr t0, mcause
    li t1, 0x80000007
    bne t0, t1, fail
    csrr t0, mstatus
    andi t1, t0, 0x88
    li t2, 0x80
    bne t1, t2, fail
    li t0, -1
    sw t0, 0(s2)
    sw t0, 4(s2)
    addi s1, s1, 1
    mret
fail:
    li t0, 0xF4300000
    li t1, 0x13333
    sw t1, 0(t0)
2:
    j 2b
