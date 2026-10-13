# Bare-metal RTOS execution

Terms used by the ThreadX example and rv32emu's bare-metal boot support.

## Language

**Bare-metal image**:
A guest program that starts without a resident operating system or firmware
and manages the processor and board directly.

**Board support package**:
The platform-specific startup and hardware support used by an RTOS kernel.
_Avoid_: Kernel port, emulator

**ThreadX kernel port**:
The processor-specific ThreadX code that saves and restores thread contexts
and implements scheduling and interrupt entry.
_Avoid_: Board support package

**ThreadX smoke test**:
A bounded run that confirms ThreadX threads execute, sleep, and resume as
kernel time advances.
_Avoid_: Boot banner test
