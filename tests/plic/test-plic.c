/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */

#include <assert.h>
#include <stdio.h>

#include "devices/plic.h"

int main(void)
{
    plic_t *plic = plic_new();
    assert(plic);

    const uint32_t irq = 5;
    const uint32_t mask = 1U << irq;

    plic_write(plic, PLIC_INTR_ENABLE_CTX1, mask);
    assert(plic_read(plic, PLIC_INTR_ENABLE) == mask);
    assert(plic_read(plic, PLIC_INTR_ENABLE_CTX1) == mask);

    plic->ip = mask;
    assert(plic_read(plic, PLIC_INTR_CLAIM_OR_COMPLETE_CTX1) == irq);
    assert(plic_read(plic, PLIC_INTR_PENDING) == 0);

    plic->masked = mask;
    plic_write(plic, PLIC_INTR_CLAIM_OR_COMPLETE_CTX1, irq);
    assert(plic->masked == 0);
    assert(plic_read(plic, PLIC_INTR_PRIORITY_THRESHOLD_CTX1) == 0);

    plic_delete(plic);
    printf("plic: context aliases share the supervisor target\n");
    return 0;
}
