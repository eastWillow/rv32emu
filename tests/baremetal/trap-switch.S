/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
/* An RTOS can leave a trap by switching to a solicited thread context and
 * returning normally, rather than by executing mret. Timer delivery must
 * continue after that switch.
 */
.section .text
.global _start
_start:
    la t0, handler
    csrw mtvec, t0
    li s0, 0
    li s1, 0xF4204000
    li s2, 0xF420BFF8
    li t0, -1
    sw t0, 0(s1)
    sw zero, 4(s1)
    sw zero, 0(s1)
    li t0, 0x80
    csrw mie, t0
    csrsi mstatus, 8
resume:
    li t0, 2
    bltu s0, t0, resume
    li t0, 0xF4300000
    li t1, 0x5555
    sw t1, 0(t0)
1:
    j 1b
.balign 4
handler:
    csrr t0, mcause
    li t1, 0x80000007
    bne t0, t1, fail
    addi s0, s0, 1
    lw t0, 0(s2)
    addi t0, t0, 1000
    sw t0, 0(s1)
    li t0, 0x1888
    csrw mstatus, t0
    /* Same return shape as ThreadX's solicited context restore. */
    la ra, resume
    ret
fail:
    li t0, 0xF4300000
    li t1, 0x13333
    sw t1, 0(t0)
2:
    j 2b
