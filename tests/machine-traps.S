/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */

/* Exercise machine trap state without requiring a board or timer device. */
.section .text
.global _start
_start:
    li t0, 0x80
    csrw mie, t0
    csrr t1, mie
    bne t0, t1, fail
    csrw mie, zero

    /* MRET must clear a previously set MIE when MPIE is zero. */
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

    /* Exceptions use the base even when MTVEC is in vectored mode.
     * Set stale MPIE beforehand; trap entry must replace it with MIE=0.
     */
    li s0, 0
    la t0, vectors
    ori t0, t0, 1
    csrw mtvec, t0
    li t0, 0x1880
    csrw mstatus, t0
fault:
    ebreak
    li t0, 1
    bne s0, t0, fail
    csrw mtvec, zero
    li a0, 1
    la a1, passed
    li a2, 22
    li a7, 64
    ecall
    li a0, 0
    j exit
fail:
    csrw mtvec, zero
    li a0, 1
exit:
    li a7, 93
    ecall

.balign 4
vectors:
    j exception
    j fail
    j fail
    j fail
exception:
    csrr t0, mcause
    li t1, 3
    bne t0, t1, fail
    csrr t0, mepc
    la t1, fault
    bne t0, t1, fail
    csrr t1, mstatus
    andi t1, t1, 0x88
    bnez t1, fail
    addi t0, t0, 4
    csrw mepc, t0
    addi s0, s0, 1
    mret

.section .rodata
passed:
    .ascii "Machine trap state OK\n"
