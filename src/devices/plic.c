/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */

#include <assert.h>
#include <stdlib.h>

#include "plic.h"
#include "riscv.h"
#include "riscv_private.h"

void plic_update_interrupts(plic_t *plic)
{
    riscv_t *rv = (riscv_t *) plic->rv;

    /* Update pending interrupts */
    plic->ip |= plic->active & ~plic->masked;
    plic->masked |= plic->active;
    /* Send interrupt to target */
    if (plic->ip & plic->ie)
        rv->csr_sip |= SIP_SEIP;
    else
        rv->csr_sip &= ~SIP_SEIP;
}

uint32_t plic_read(plic_t *plic, const uint32_t addr)
{
    uint32_t plic_read_val = 0;

    switch (addr) {
    case PLIC_INTR_PENDING:
        plic_read_val = plic->ip;
        break;
    case PLIC_INTR_ENABLE:
    case PLIC_INTR_ENABLE_CTX1:
        plic_read_val = plic->ie;
        break;
    case PLIC_INTR_PRIORITY_THRESHOLD:
    case PLIC_INTR_PRIORITY_THRESHOLD_CTX1:
        /* no priority support: target priority threshold hardwired to 0 */
        plic_read_val = 0;
        break;
    case PLIC_INTR_CLAIM_OR_COMPLETE:
    case PLIC_INTR_CLAIM_OR_COMPLETE_CTX1:
        /* claim */
        {
            uint32_t intr_candidate = plic->ip & plic->ie;
            if (intr_candidate) {
                plic_read_val = rv_ctz(intr_candidate);
                plic->ip &= ~(1U << (plic_read_val));
            }
            break;
        }
    default:
        return 0;
    }

    return plic_read_val;
}

void plic_write(plic_t *plic, const uint32_t addr, uint32_t value)
{
    switch (addr) {
    case PLIC_INTR_ENABLE:
    case PLIC_INTR_ENABLE_CTX1:
        plic->ie = (value & ~1);
        break;
    case PLIC_INTR_PRIORITY_THRESHOLD:
    case PLIC_INTR_PRIORITY_THRESHOLD_CTX1:
        /* no priority support: target priority threshold hardwired to 0 */
        break;
    case PLIC_INTR_CLAIM_OR_COMPLETE:
    case PLIC_INTR_CLAIM_OR_COMPLETE_CTX1:
        /* completion */
        if (plic->ie & (1U << value))
            plic->masked &= ~(1U << value);
        break;
    default:
        break;
    }

    return;
}

plic_t *plic_new(void)
{
    plic_t *plic = calloc(1, sizeof(plic_t));
    assert(plic);

    return plic;
}

void plic_delete(plic_t *plic)
{
    free(plic);
}

void plic_reset(plic_t *plic)
{
    memset(plic, 0, sizeof(plic_t));
}
