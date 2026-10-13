# Zephyr validation on RV32EMU and QEMU

Validated on 2026-10-13 (Asia/Taipei), based on `fix/zephyr-s-mode-csr` at
`906e73b7a9d3e821f07cd20d8f3784eb5bfaa05d`. The validation change adds tooling
and evidence on top of that emulator core revision.

## Coverage

Twister inventoried 5,035 configurations across tests and samples. Shared
sample dependencies are deduplicated; distinct toolchains retain separate
configuration identities. Every eligible automatic run completed.

| Main GCC profile, per engine | Tests | Samples |
| --- | ---: | ---: |
| Passed configurations | 464 | 78 |
| Built, not run | 19 | 24 |
| Filtered | 3,186 | 1,263 |
| Build errors | 0 | 1 |
| Runtime failures / timeouts / unfinished | 0 | 0 |

Both engines passed 5,254 individual test cases, with 276 skipped cases.
Passing suites also contain 487 discovered cases per engine without a reported
verdict. These are preserved in [unreported-cases.csv](unreported-cases.csv)
and are not counted as individual passes. This is the supported automatic
RV32 S-mode profile, not complete coverage of every Zephyr board or test case.

The GCC sample build error is `sample.cpp.helloworld`: the distribution RISC-V
GCC lacks the full C++ library headers. A separate xPack 15.2.0/newlib profile
with native TLS disabled passed that sample on both engines. Its GCC error
remains visible in the main report. Thus 79 distinct samples were exercised
across the two explicitly separated toolchain profiles.

Each emulator completed the one-hour guest-time timer starvation soak. The
branch boot harness also freshly passed hello_world and 38 alternating
synchronization lines for each prepared GCC and xPack CI guest. Those four
prepared guest images were reused; the emulator was freshly built.

## Repeated completion-time demonstration

Each workload ran seven times per engine, serially with alternating engine
order. Every run completed the same ztest suites and case outcomes. Timings
measure guest process launch to final verdict, including firmware startup
and Zephyr boot. Compilation and comparison-wrapper startup are excluded.

| Fixed workload | QEMU median | RV32EMU median | QEMU / RV32EMU time |
| --- | ---: | ---: | ---: |
| `libraries.nanopb` | 52.927 ms | 5.306 ms | 9.976 |
| `kernel.mutex` | 75.918 ms | 28.084 ms | 2.703 |
| `libraries.heap` | 4474.460 ms | 5149.504 ms | 0.869 |

Nanopb completion was about 10 times quicker on RV32EMU in this setup. The
heap workload was slower on RV32EMU; it uses a fixed allocation iteration
count and a deterministic seed. Raw repetitions and case signatures are in
[the Nanopb data](demo-libraries.nanopb.json), [mutex data](demo-kernel.mutex.json),
and [heap data](demo-libraries.heap.json).

## Whole-campaign time

| Engine | Serial GCC test and sample phases |
| --- | ---: |
| qemu | 1133.91 s (18.90 min) |
| rv32emu | 1432.02 s (23.87 min) |

RV32EMU took 1.263 times as long for the full main campaign.
These totals include Twister/harness overhead, startup, and timer/sleep policy.
They exclude compilation, pilots, the C++ supplement, repeated demonstrations,
and the metadata followup. The short-workload speedup is an end-to-end result;
it does not establish a universal CPU throughput advantage.

## Sources and method

- System interpreter, Goldfish RTC enabled, virtio networking disabled.
- Zephyr `bbc6385f0a2c6476b5f191b3101d902303a34f50` with the explicit
  [comparison patch](../../../.ci/zephyr/compare/zephyr.patch). The patch
  selects PLIC contexts, preserves hardware overlays, and adapts the coredump
  test to RAM mapped at zero. That adapted coredump test is included in coverage.
- Main guests use GCC 14.2.0, RV32IMAC/soft-float, single-core S-mode and native
  TLS. QEMU 10.2.1 uses RV32 OpenSBI with deterministic `icount`; RV32EMU uses
  its built-in SBI. Memory maps and clocks differ (10 MHz versus 65 MHz).
- Reused 454 QEMU and 439 RV32EMU pinned-source guest builds; each was freshly
  executed. Missing builds, remaining eligible configurations and samples were
  built in the new worktree. Reused builds reduce compilation work and are
  excluded from execution-speed measurements.
- Fixed shutdown metadata loss for verbose console output with interruptible
  forwarding; the philosopher static sample passed its focused replay and
  produced a complete metadata record.
- Native unit/source integration checks and 744/744 decoder verification passed.
  Black 25.1.0, shfmt, dtsfmt 0.8.0, Python/shell syntax and Git whitespace
  checks passed for the additions.

Full outcomes and reasons: [comparison.csv](comparison.csv). Counts and phase
durations: [summary.json](summary.json). Source/module revisions and binary
hashes: [provenance.json](provenance.json). Final record/hash audit:
[verification.json](verification.json). All console logs, Twister reports,
commands, and per-guest hashes remain in the worktree under
`build/zephyr-validation/`. Reproduction commands are in
[zephyr-compare.md](../../zephyr-compare.md).

A later full rebuild and runtime campaign under explicit CPU/memory limits is
recorded in [the resource-limited rerun report](resource-rerun/REPORT.md).
