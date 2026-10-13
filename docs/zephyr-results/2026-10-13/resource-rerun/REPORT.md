# Resource-limited Zephyr/QEMU rerun

Completed 2026-10-13, Asia/Taipei. This full rerun validates branch
`test/zephyr-qemu-validation` at `32ae0b2989756f9bf7cc13cc33588f804174d394`,
on top of `fix/zephyr-s-mode-csr` at `906e73b7a9d3e821f07cd20d8f3784eb5bfaa05d`.
Both campaign and external resource observer exited successfully. All 14
phases completed; the final audit checked original scope and current evidence.

## Coverage and boot checks

Each engine inventoried the same 5,035 configuration identities and freshly
built the eligible GCC inventory, allowing ccache. No previously built main
campaign ELF files were reused. Tests and samples have matching outcomes:

| Main GCC profile, per engine | Tests | Samples | Total |
| --- | ---: | ---: | ---: |
| Passed configurations | 464 | 78 | 542 |
| Built, not run | 19 | 24 | 43 |
| Filtered | 3,186 | 1,263 | 4,449 |
| Build errors | 0 | 1 | 1 |
| Runtime failures / errors | 0 | 0 | 0 |

The preserved GCC error is `sample.cpp.helloworld`, missing `string.h` in
its configured Newlib sysroot. The separate xPack C++ build and runtime passed
on both engines with native TLS disabled. This exercises 79 distinct samples
across the two explicit compiler profiles.

Per engine, the 464 test configurations report 5,254 passed cases, 276 skipped,
and 487 discovered cases without verdicts. The 78 GCC sample configurations
add 78 passing sample cases: the combined main report has **5,332** passes.
The C++ supplement adds one pass. Unreported cases remain uncounted as passes;
see [unreported-cases.csv](unreported-cases.csv).

Both timer-starvation soak configurations passed. The four prepared GCC/xPack
RV32EMU CI boot checks passed hello_world and exactly 38 alternating
synchronization lines per compiler. These four CI binaries were reused and
verified against prior hashes; main campaign guests were freshly built.

The audit checked 543 guest records per engine against actual ELF/bin hashes
and console logs. Each engine has 439 runner ztest verdicts and 104
`harness_stop` records where Twister's console/sample harness determines the
pass. A harness stop alone is not a ztest completion verdict. Twister reports
prove the full supported automatic S-mode profile; filters and build-only
configurations remain explicit, rather than being counted as runtime passes.

## CPU and memory

The campaign ran in one systemd cgroup at CPU quota 150% (1.5 cores), affinity
10/11, nice 10, one Twister job, and two compiler jobs. The guest runner pinned
each guest to CPU 10. MemoryHigh was 1.5 GiB, MemoryMax 2 GiB, swap max zero,
and TasksMax 128. The external monitor sampled every two seconds. A guard
would stop only this campaign if host available memory stayed below 2 GiB
for ten seconds; it never fired.

| Observed resource | Result |
| --- | ---: |
| Peak charged cgroup memory | 1.501919 GiB |
| Peak summed process RSS | 1168.67 MiB |
| Peak summed process PSS | 952.70 MiB |
| Minimum host available memory | 6.719 GiB |
| Campaign swap use | 0 bytes |
| Hard memory-limit events / OOM / OOM kills | 0 / 0 / 0 |
| Resource samples | 19,579 |
| Longest sampling gap | 2.299 seconds |
| Whole controller elapsed time | 11.406 hours |

Charged memory includes page cache and kernel accounting; it is distinct from
resident process memory. Soft-limit events (255,723)
reflect reclaim/throttling around MemoryHigh. The peak briefly exceeded the
soft limit, while staying below the hard limit. CPU quota was verified in
every recorded limits sample. The largest short sample was
151.512% of one core;
sampling boundaries can slightly exceed 150% even though the kernel enforces
150,000 microseconds per 100,000-microsecond period. Existing host swap use is
recorded separately and is not attributed to this zero-swap cgroup.

The first observer sample followed controller start by 0.203 seconds; monitoring
continued through terminal status. Two-second samples cannot resolve every
instantaneous fluctuation; the kernel's final MemoryPeak is also preserved.
Raw observations: [resources.jsonl.gz](resources.jsonl.gz).
Tabular observations: [resources.csv.gz](resources.csv.gz).

## Repeated completion-time comparisons

All three workloads ran seven times per engine, alternating engine order.
All 42 runs matched suite/case outcomes and verified the actual guest hashes.
These host times include firmware startup and Zephyr boot, and exclude
compilation and Python comparison-wrapper startup.

| Workload | QEMU median | RV32EMU median | QEMU / RV32EMU |
| --- | ---: | ---: | ---: |
| `libraries.nanopb` | 75.748 ms | 7.434 ms | 10.189 |
| `kernel.mutex` | 109.560 ms | 39.292 ms | 2.788 |
| `libraries.heap` | 6902.602 ms | 7910.897 ms | 0.873 |

RV32EMU is about 10.19 times faster for nanopb and 2.79 times faster for mutex
in this setup. Heap is 14.6% slower on RV32EMU. This is an end-to-end workload
comparison, not a universal CPU throughput claim.

The main serial runtime phase took 3485.281 s
(58.09 min) on RV32EMU and
3128.896 s
(52.15 min) on QEMU. These totals
include Twister/harness overhead and timer/sleep policy; they exclude builds,
C++ supplement, demos, and prepared boot checks. RV32EMU was
1.114 times as long overall.

## Reproducibility and evidence

Zephyr, all 15 modules, OpenSBI, documented guest adaptations, and the emulator
binary matched the pinned inputs. The system interpreter configuration has
RTC enabled and virtio networking disabled. QEMU 10.2.1 uses RV32 OpenSBI and
`icount shift=6`; RV32EMU uses built-in SBI. Memory maps and guest clocks differ
(QEMU 10 MHz, RV32EMU 65 MHz), and affect timing. Main guests use GCC 14.2.0;
the explicit xPack C++ supplement uses 15.2.0/newlib.

- [Full configuration outcomes](outcomes.csv)
- [Phase results, coverage, and resource aggregate](summary.json)
- [Source and module provenance](provenance.json)
- [Final audit](verification.json)
- [Guest records and console hashes](guest-records.json)
- [All 42 timing observations](timings.csv)
- [Original campaign and its results](../REPORT.md)

Full local guest consoles, build logs, systemd control/observer scripts, and
original Twister reports remain under `build/zephyr-resource-rerun/` in the
validation worktree. The controller and observer were inspected against their
recorded commands and resource policies. Shared campaign reproduction tools
are described in [zephyr-compare.md](../../../zephyr-compare.md).
