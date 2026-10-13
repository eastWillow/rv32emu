/*
 * rv32emu is freely redistributable under the MIT License. See the file
 * "LICENSE" for information on usage and redistribution of this file.
 */
#include "board.h"
#include "tx_api.h"

static TX_THREAD threads[2];
static TX_TIMER timer;
static _Alignas(16) unsigned char stacks[2][2048];
static volatile ULONG runs[2];
static volatile ULONG callbacks;

static void timer_callback(ULONG input)
{
    (void) input;
    callbacks++;
}

static void worker(ULONG id)
{
    for (;;) {
        runs[id]++;
        if (runs[0] >= 5 && runs[1] >= 5 && callbacks >= 3 &&
            tx_time_get() >= 10) {
            board_puts("ThreadX smoke test PASS\n");
            board_exit(0);
        }
        if (tx_thread_sleep(id + 2) != TX_SUCCESS) {
            board_puts("ThreadX sleep FAIL\n");
            board_exit(1);
        }
    }
}

void tx_application_define(void *unused_memory)
{
    (void) unused_memory;
    for (ULONG id = 0; id < 2; id++) {
        if (tx_thread_create(&threads[id], id ? "worker 1" : "worker 0", worker,
                             id, stacks[id], sizeof(stacks[id]), id + 1, id + 1,
                             TX_NO_TIME_SLICE, TX_AUTO_START) != TX_SUCCESS)
            board_exit(1);
    }
    if (tx_timer_create(&timer, "smoke timer", timer_callback, 0, 2, 2,
                        TX_AUTO_ACTIVATE) != TX_SUCCESS)
        board_exit(1);
}

int main(void)
{
    board_puts("ThreadX starting in machine mode\n");
    tx_kernel_enter();
    board_exit(1);
}
