/* A timer that becomes pending in a learned branch loop must be delivered. */
.option norvc
.section .text
.global _start

.equ UART, 0xf4000000

_start:
    li s0, UART
    la t0, trap
    csrw stvec, t0
    li t0, 32
    csrw sie, t0
    rdtime a0
    li t0, 10000
    add a0, a0, t0
    li a1, 0
    li a6, 0
    li a7, 0x54494d45          /* SBI set timer */
    ecall
    li t0, 2
    csrw sstatus, t0
busy:
    j busy

.balign 4
trap:
    csrr t0, scause
    li t1, 0x80000005
    bne t0, t1, fail
    la a0, pass
    j finish
fail:
    la a0, failure
finish:
    jal ra, puts
    li a0, 0
    li a1, 0
    li a6, 0
    li a7, 0x53525354
    ecall
stop:
    j stop

puts:
    lbu t0, 0(a0)
    beqz t0, 2f
    sb t0, 0(s0)
    addi a0, a0, 1
    j puts
2:
    ret

.section .rodata
pass:    .asciz "PASS timer-chain\n"
failure: .asciz "FAIL timer-chain: unexpected trap\n"
