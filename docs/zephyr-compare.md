# Verify Zephyr and compare QEMU completion time

On a Linux host, use the system interpreter and the same GCC-built RV32IMAC
S-mode workloads
on RV32EMU and QEMU. Twister owns scenario eligibility, console patterns,
test-case verdicts, and timeouts. Build-only and filtered configurations stay
visible in its JSON reports.

## Prepare the guests

Use Zephyr `bbc6385f0a2c6476b5f191b3101d902303a34f50`, picolibc
`ad4203cecf0fd65f653835fe65c20f1b7924e0ca`, GCC 14.2.0, and the modules
required by the scenarios. Install the pinned Zephyr checkout's Python
requirements into a virtual environment and activate it. Install CMake,
Ninja, dtc, QEMU with RV32 system support, and RV32 OpenSBI firmware.

Apply `.ci/zephyr/compare/zephyr.patch` to a separate Zephyr checkout at that
revision. The patch makes the PLIC context selectable (QEMU 1, RV32EMU 0),
preserves the simulator overlay when tests add overlays, and makes the
coredump test call `k_panic()` on a board whose RAM starts at zero. A null
pointer addresses valid RAM on that board. These are explicit guest
adaptations; broad campaign results include this patched test.

```sh
make system_interpreter_defconfig
make CONFIG_VIRTIO_NET=n -j8
export ZEPHYR_BASE=/absolute/path/to/patched-zephyr
git -C "$ZEPHYR_BASE" apply "$PWD/.ci/zephyr/compare/zephyr.patch"
export CROSS_COMPILE=/usr/bin/riscv64-unknown-elf-
export ZEPHYR_MODULES='/absolute/path/to/picolibc;/absolute/path/to/other-module'
export OPENSBI=/absolute/path/to/rv32/fw_dynamic.bin
export RV32EMU="$PWD/build/rv32emu"
export CMAKE_BUILD_PARALLEL_LEVEL=2
```

Both engines use native TLS, one CPU, and soft-float RV32IMAC. The board
selects S-mode and external SBI. RV32EMU loads a raw binary at zero and
uses its built-in SBI; QEMU loads an ELF at `0x80400000` after OpenSBI.
UART, PLIC, and timer mappings differ. RV32EMU's clock is 65 MHz; QEMU's
clock is 10 MHz and uses Zephyr's deterministic `icount` configuration.

## Inventory, build, and run

The helper inventories both `tests/` and `samples/`. Hardware requirements,
platform allow lists, runtime Kconfig filters, and harness availability
limit what this board can execute. Review the recorded reasons instead of
counting filtered or build-only configurations as passing executions.

```sh
.ci/compare-zephyr.sh rv32emu build/compare-rv --dry-run
.ci/compare-zephyr.sh qemu build/compare-qemu --dry-run
.ci/compare-zephyr.sh rv32emu build/compare-rv --build-only -j4
.ci/compare-zephyr.sh qemu build/compare-qemu --build-only -j4
.ci/compare-zephyr.sh rv32emu build/compare-rv --test-only -j1
.ci/compare-zephyr.sh qemu build/compare-qemu --test-only -j1
```

Run the two test phases sequentially after both builds finish. The runner
pins guests to the first available host CPU. Each output contains Twister
reports plus `guest-runs/` console logs, commands, guest hashes, and host
timing. Console harnesses use Twister's verdict; the wrapper's
`harness_stop` does not independently mean success.

## Full C++ library sample

The distribution GCC used for the main campaign lacks the full C++ library
needed by `sample.cpp.helloworld`. Its failed build remains in the GCC report.
To validate that sample on both engines with xPack 15.2.0, use a separate
profile with its bundled newlib/libstdc++ and disable native TLS:

```sh
export CROSS_COMPILE=/absolute/path/to/xpack/bin/riscv-none-elf-
for engine in rv32emu qemu; do
  .ci/compare-zephyr.sh "$engine" "build/cpp-$engine" \
    -s sample.cpp.helloworld --build-only -j1 \
    -x SYSROOT_DIR=/absolute/path/to/xpack/riscv-none-elf \
    -x TOOLCHAIN_HAS_NEWLIB=ON \
    -x "EXTRA_CONF_FILE=$PWD/.ci/zephyr/no-tls.conf"
  .ci/compare-zephyr.sh "$engine" "build/cpp-$engine" --test-only -j1
done
```

Keep this result separate from the main GCC/native-TLS comparison.

## Repeat a speed demonstration

Choose an identical fixed-work ztest scenario on both engines, such as
`libraries.nanopb`. Keep a slower scenario in the comparison evidence as
well. Pass each engine's generated ELF and raw binary:

```sh
python .ci/zephyr/compare-demo.py \
  --qemu-elf /absolute/path/to/qemu/zephyr.elf \
  --qemu-bin /absolute/path/to/qemu/zephyr.bin \
  --rv32emu-elf /absolute/path/to/rv32emu/zephyr.elf \
  --rv32emu-bin /absolute/path/to/rv32emu/zephyr.bin \
  --out build/compare-demo --repeat 7
```

The demonstration alternates engine order, runs serially, and requires the
ztest success marker and matching test-case outcomes on every repetition.
It measures host launch to final
verdict, including firmware startup and Zephyr boot. Comparison-wrapper
startup and compilation are excluded. The median ratio
expresses end-to-end completion speed for that workload. It does not isolate
CPU execution speed; timer policy and startup costs influence the result.
The broader campaign retains all slower workloads and unsuccessful results.

The [2026-10-13 validation report](zephyr-results/2026-10-13/REPORT.md)
contains measured outcomes, coverage limits, and repeated speed comparisons.
