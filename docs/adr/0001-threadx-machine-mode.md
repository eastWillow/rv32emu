# Preserve the upstream ThreadX RV32 machine-mode port

Run ThreadX through an explicit, interpreter-only bare-metal boot option in
rv32emu. Reuse the upstream RV32 GNU port with a small board support package
for rv32emu's RAM and UART, and add a machine timer. Adapting the kernel to
supervisor mode would require maintaining changes throughout its RV32
context-switch code; reproducing QEMU's entire board would add peripherals
this example does not need. Keep ThreadX as a configurable external checkout
so its source and revision remain independently reviewable.
