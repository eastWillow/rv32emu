/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include "system.h"

/* Exercise the actual device handlers, including the equality boundary and
 * RV32 split-register writes, independently of interrupt polling latency.
 */
int main(void)
{
    vm_attr_t attr = {.data.system.baremetal = true, .mtimecmp = UINT64_MAX};
    riscv_t *rv = calloc(1, sizeof(*rv));
    assert(rv);
    rv->data = &attr;
    uint32_t value;

    rv->csr_cycle = 100;
    emu_update_mtimer(rv);
    assert(!(rv->csr_mip & RV_INT_MTI));
    attr.mtimecmp = 101;
    emu_update_mtimer(rv);
    assert(!(rv->csr_mip & RV_INT_MTI));
    rv->csr_cycle = 101;
    emu_update_mtimer(rv);
    assert(rv->csr_mip & RV_INT_MTI); /* Equality must fire. */
    rv->csr_cycle = 102;
    emu_update_mtimer(rv);
    assert(rv->csr_mip & RV_INT_MTI);

    assert(baremetal_mmio_write(rv, MTIMER_BASE + 0x4000, 4, UINT32_MAX));
    assert(baremetal_mmio_write(rv, MTIMER_BASE + 0x4004, 4, 2));
    assert(baremetal_mmio_write(rv, MTIMER_BASE + 0x4000, 4, 3));
    assert(attr.mtimecmp == UINT64_C(0x200000003));
    assert(!(rv->csr_mip & RV_INT_MTI));
    assert(baremetal_mmio_read(rv, MTIMER_BASE + 0x4000, 4, &value));
    assert(value == 3);
    assert(baremetal_mmio_read(rv, MTIMER_BASE + 0x4004, 4, &value));
    assert(value == 2);

    assert(baremetal_mmio_write(rv, MTIMER_BASE + 0xBFFC, 4, 1));
    assert(baremetal_mmio_write(rv, MTIMER_BASE + 0xBFF8, 4, UINT32_MAX));
    rv->csr_cycle++;
    assert(baremetal_mmio_read(rv, MTIMER_BASE + 0xBFF8, 4, &value));
    assert(value == 0);
    assert(baremetal_mmio_read(rv, MTIMER_BASE + 0xBFFC, 4, &value));
    assert(value == 2); /* Carry across the low word. */

    attr.data.system.baremetal = false;
    assert(!baremetal_mmio_write(rv, FINISHER_BASE, 4, 0x5555));
    assert(!rv->halt);
    attr.data.system.baremetal = true;
    assert(baremetal_mmio_write(rv, FINISHER_BASE, 4, 0x5555));
    assert(rv->halt && attr.exit_code == 0);
    rv->halt = false;
    assert(baremetal_mmio_write(rv, FINISHER_BASE, 4, 0x1003333));
    assert(rv->halt && attr.exit_code > 0 && attr.exit_code < 256);
    rv->halt = false;
    attr.exit_code = 0;
    assert(baremetal_mmio_read(rv, MTIMER_BASE, 1, &value));
    assert(rv->halt && attr.exit_code != 0);
    free(rv);
    puts("Bare-metal timer tests passed");
    return 0;
}
