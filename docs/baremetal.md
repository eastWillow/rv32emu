# Bare-metal boot

`-M` loads a raw binary at RAM address zero and starts the single hart there
in machine mode. Guest startup initializes its stack, global pointer, BSS,
and trap vector. Unlike Linux boot through `-k`, this path supplies no DTB,
initrd, or supervisor firmware services. Linux boot options cannot be combined
with `-M`.

The first version supports the native interpreter. JIT builds reject `-M`.
Interblock chaining is bypassed for bare-metal guests so machine interrupts
are checked at each block boundary. Timer ticks follow emulated cycles,
rather than wall-clock time; the guest chooses its timer compare interval.
Interrupt delivery can be delayed until the current block ends, so this is
a functional RTOS demonstration,
not a real-time timing model.

| Address | Register | Access |
| --- | --- | --- |
| `0x00000000` | Start of RAM and image entry point | Guest RAM |
| `0xF4000000` | Existing 8250 UART | Byte registers |
| `0xF4204000`, `0xF4204004` | Low/high halves of `mtimecmp` | 32-bit read/write |
| `0xF420BFF8`, `0xF420BFFC` | Low/high halves of `mtime` | 32-bit read/write |
| `0xF4300000` | Test finisher | 32-bit read/write |

The machine timer uses the CLINT timer register offsets relocated to
rv32emu's MMIO window. It asserts `mip.MTIP` when `mtime >= mtimecmp`, with
`mtimecmp` initially set to all ones. Use the RV32 safe compare write
sequence (low all ones, high, then low) and a high/low/high time read.
Software and external machine interrupts are outside this initial board
support package; guests enable `mie.MTIE` to receive timer interrupts.

The finisher returns zero on reads. Writing `0x5555` exits successfully.
Writing `(code << 16) | 0x3333` exits with a nonzero status; codes outside
1–255 become status 1. Unsupported accesses to the timer or finisher also
fail the run. A machine exception before configuring `mtvec` fails instead
of retrying indefinitely.

Machine traps return to the emulator dispatcher after trap entry. ThreadX
can resume a solicited thread context with an ordinary return instead of
`mret`; executing the entire handler inline until `mret` would miss later
timer checks after such a switch.

## Build and check

```sh
make baremetal_defconfig
make -j4 tests check-baremetal
build/rv32emu -M /path/to/guest.bin
```

Use the usual system-build dependencies and an RV32-capable bare-metal GCC
toolchain. `BAREMETAL_CROSS_COMPILE` defaults to `riscv64-unknown-elf-` and
can be overridden for another compiler prefix. No external RTOS checkout
is required by these regression tests.

`check-baremetal` checks timer equality, split-register writes and rollover,
masked interrupts, vectored trap dispatch, `mret`, continued timer delivery
after a solicited context switch, finisher statuses, and rejected boot options.
