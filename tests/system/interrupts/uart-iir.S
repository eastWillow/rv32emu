/* Verify 8250 interrupt identification without a guest operating system. */
.option norvc
.section .text
.global _start

.equ UART, 0xf4000000
.equ UART_RBR, 0
.equ UART_IER, 1
.equ UART_IIR, 2
.equ UART_LSR, 5

_start:
    li s0, UART
    li t0, 3
    sb t0, UART_IER(s0)        /* enable RX and THR-empty interrupts */
    la a0, ready
    jal ra, puts

wait_for_input:
    csrw sscratch, zero        /* dispatcher boundary before CSR fix */
    lbu t0, UART_LSR(s0)
    andi t0, t0, 1
    beqz t0, wait_for_input

    lbu t0, UART_IIR(s0)
    li t1, 0x04
    bne t0, t1, fail_rx
    lbu t0, UART_IIR(s0)       /* RX remains pending until RBR is read */
    bne t0, t1, fail_rx
    lbu t0, UART_RBR(s0)
    li t1, 'U'
    bne t0, t1, fail_data

    /* UART readiness is sampled periodically by the dispatcher. */
    li t2, 128
refresh:
    csrw sscratch, zero
    addi t2, t2, -1
    bnez t2, refresh

    lbu t0, UART_IIR(s0)
    li t1, 0x02
    bne t0, t1, fail_thre
    lbu t0, UART_IIR(s0)
    li t1, 0x01
    bne t0, t1, fail_idle
    la a0, pass
    j finish

fail_rx:
    la a0, rx_error
    j finish
fail_data:
    la a0, data_error
    j finish
fail_thre:
    la a0, thre_error
    j finish
fail_idle:
    la a0, idle_error

finish:
    jal ra, puts
    li a0, 0
    li a1, 0
    li a6, 0
    li a7, 0x53525354          /* SBI system reset */
    ecall
stop:
    j stop

puts:
    lbu t0, 0(a0)
    beqz t0, 2f
    sb t0, UART_RBR(s0)
    addi a0, a0, 1
    j puts
2:
    ret

.section .rodata
ready:      .asciz "UART-READY\n"
pass:       .asciz "PASS uart-iir\n"
rx_error:   .asciz "FAIL uart-iir: receive identification\n"
data_error: .asciz "FAIL uart-iir: receive data\n"
thre_error: .asciz "FAIL uart-iir: transmitter identification\n"
idle_error: .asciz "FAIL uart-iir: idle identification\n"
