OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY { RAM (rwx) : ORIGIN = 0, LENGTH = 1M }
PHDRS { text PT_LOAD FLAGS(5); data PT_LOAD FLAGS(6); }
SECTIONS
{
    .text : { KEEP(*(.text.boot)) *(.text .text.*) } > RAM :text
    .rodata : { *(.rodata .rodata.* .srodata .srodata.*) } > RAM :text
    .data : {
        . = ALIGN(16);
        __global_pointer$ = . + 0x800;
        *(.sdata .sdata.* .data .data.*)
    } > RAM :data
    .bss (NOLOAD) : {
        . = ALIGN(16);
        _bss_start = .;
        *(.sbss .sbss.* .bss .bss.* COMMON)
        . = ALIGN(16);
        _bss_end = .;
    } > RAM :data
    .stack (NOLOAD) : {
        . = ALIGN(16);
        . += 4096;
        _stack_top = .;
    } > RAM :data
    _end = .;
}
