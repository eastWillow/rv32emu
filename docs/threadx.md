# ThreadX on rv32emu

The example boots the upstream ThreadX RV32 GNU kernel port in machine mode.
Two threads at different priorities sleep for two and three kernel ticks.
The run prints `ThreadX smoke test PASS` and exits successfully only after
both threads have run at least five times, kernel time has advanced at least
ten ticks, and a periodic ThreadX timer has called back at least three times.
The host runner requires that marker and a zero exit status within 20 seconds.

## Build and run

Install the normal rv32emu system-build dependencies, including a device tree
compiler, plus CMake and a bare-metal RISC-V GCC toolchain with RV32 `ilp32`
multilib support. The default compiler prefix is `riscv64-unknown-elf-`.
No target C library is needed: this example supplies the `memset` required by
ThreadX. The guest uses `rv32ima_zicsr` and the soft-float `ilp32` ABI.

From the rv32emu repository:

```sh
make baremetal_defconfig
make -j4 check-threadx THREADX_DIR=../threadx
```

The default `THREADX_DIR` is the sibling `../threadx` checkout. The build puts
all objects and generated files under `build/threadx`; it does not change or
fetch the ThreadX source. To use another compiler prefix or bound compilation
parallelism:

```sh
make threadx THREADX_DIR=/path/to/threadx \
    THREADX_CROSS_COMPILE=riscv32-unknown-elf- THREADX_JOBS=4
```

For a manual run after building:

```sh
build/rv32emu -M build/threadx/threadx-demo.bin
```

This example was tested against ThreadX revision
`93387b0a60382a29579bbad5045c68328e3751df`. Use that revision to reproduce the
validated build; a different checkout may require changes to the example.
The supplied startup and board code override ThreadX's weak initialization
routine while compiling the upstream kernel and context-switch sources.

## Board support package

The example uses rv32emu's [bare-metal boot interface](baremetal.md): RAM
at zero, the existing UART, the machine timer, and the test finisher.
The board support package rearms the timer for one ThreadX tick per 1,000
emulated cycles. This is a functional scheduling check, not a real-time
timing model. `startup.S` supplies reset and trap entry; `board.c` handles
UART output and timer interrupts; `demo.c` owns the ThreadX smoke test.

## Regression checks

```sh
make -j4 tests check-baremetal check-threadx THREADX_DIR=../threadx
```

`check-baremetal` does not require ThreadX; its checks are described in
[bare-metal boot](baremetal.md#build-and-check). The existing host component
tests run through `make tests`.
