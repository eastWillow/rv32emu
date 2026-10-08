/* A pending interrupt must be taken immediately after an enabling CSR write. */
.option norvc
.section .text
.global _start

.equ UART, 0xf4000000
.equ SSTATUS_SIE, 2
.equ SSIP, 2

_start:
    li s0, UART
    la t0, trap
    csrw stvec, t0
    li t0, SSIP
    csrw sie, t0

    /* CSRRS */
    li s1, 0
    li s2, 0
    csrs sip, t0
    csrs sstatus, t0
    addi s1, s1, 1
    csrr t1, sstatus
    beqz s2, fail_missing

    /* CSRRSI */
    csrci sstatus, SSTATUS_SIE
    li s1, 0
    li s2, 0
    csrs sip, t0
    csrsi sstatus, SSTATUS_SIE
    addi s1, s1, 1
    csrr t1, sstatus
    beqz s2, fail_missing

    /* CSRRW */
    csrci sstatus, SSTATUS_SIE
    li s1, 0
    li s2, 0
    csrs sip, t0
    csrw sstatus, t0
    addi s1, s1, 1
    csrr t1, sstatus
    beqz s2, fail_missing

    /* CSRRWI */
    csrci sstatus, SSTATUS_SIE
    li s1, 0
    li s2, 0
    csrs sip, t0
    csrwi sstatus, SSTATUS_SIE
    addi s1, s1, 1
    csrr t1, sstatus
    beqz s2, fail_missing

    la a0, pass
    j finish

.balign 4
trap:
    csrr t1, scause
    li t2, 0x80000001
    bne t1, t2, fail_cause
    bnez s1, fail_late
    csrc sip, t0
    li s2, 1
    sret

fail_late:
    la a0, late
    j finish
fail_missing:
    la a0, missing
    j finish
fail_cause:
    la a0, cause

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
    lbu t1, 0(a0)
    beqz t1, 2f
    sb t1, 0(s0)
    addi a0, a0, 1
    j puts
2:
    ret

.section .rodata
pass:    .asciz "PASS csr-pending\n"
late:    .asciz "FAIL csr-pending: next instruction executed\n"
missing: .asciz "FAIL csr-pending: interrupt missing\n"
cause:   .asciz "FAIL csr-pending: unexpected cause\n"
