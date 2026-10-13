/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */

#include <assert.h>
#include <stdio.h>

#include "devices/plic.h"

static void test_completion_bounds(plic_t *plic)
{
    const uint32_t offsets[] = {PLIC_INTR_CLAIM_OR_COMPLETE,
                                PLIC_INTR_CLAIM_OR_COMPLETE_CTX1};
    const uint32_t invalid_ids[] = {0, 32, 37, UINT32_MAX};

    for (size_t i = 0; i < sizeof(offsets) / sizeof(offsets[0]); i++) {
        plic->ie = UINT32_MAX & ~1U;
        plic->masked = plic->ie;
        for (size_t j = 0; j < sizeof(invalid_ids) / sizeof(invalid_ids[0]);
             j++) {
            plic_write(plic, offsets[i], invalid_ids[j]);
            assert(plic->masked == plic->ie);
        }

        plic_write(plic, offsets[i], 31);
        assert(plic->masked == (plic->ie & ~(1U << 31)));
        plic_write(plic, offsets[i], 1);
        assert(plic->masked == (plic->ie & ~(1U << 31) & ~(1U << 1)));

        plic->ie = 1U << 5;
        plic->masked = 1U << 6;
        plic_write(plic, offsets[i], 6);
        assert(plic->masked == (1U << 6));
    }
}

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

    test_completion_bounds(plic);
    plic_delete(plic);
    printf("plic: context aliases share the supervisor target\n");
    return 0;
}
