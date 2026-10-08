#!/usr/bin/env bash

# Build a reproducible Apache NuttX system-mode image for rv32emu.
set -e -u -o pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
RV32EMU_ROOT=$(cd -- "${SCRIPT_DIR}/.." && pwd)
. "${RV32EMU_ROOT}/.ci/common.sh"

NUTTX_DIR=${NUTTX_DIR:-/tmp/nuttx}
NUTTX_APPS_DIR=${NUTTX_APPS_DIR:-/tmp/nuttx-apps}
NUTTX_REVISION=${NUTTX_REVISION:-6e41066215f7d46832bcded77e93bed1fc04092e}
NUTTX_APPS_REVISION=${NUTTX_APPS_REVISION:-1f8cac8b87a925403340947582b026cf2a117423}
OUTPUT_DIR=${OUTPUT_DIR:-${RV32EMU_ROOT}/build/nuttx-image}

verify_revision()
{
    local directory=$1
    local expected=$2
    local actual
    actual=$(git -C "${directory}" rev-parse HEAD)
    if [ "${actual}" != "${expected}" ]; then
        print_error "${directory} is at ${actual}; expected ${expected}"
        exit 1
    fi
}

find_cross_prefix()
{
    local candidate
    for candidate in "${CROSS_COMPILE:-}" riscv-none-elf- riscv64-unknown-elf-; do
        [ -n "${candidate}" ] || continue
        if command -v "${candidate}gcc" >/dev/null 2>&1 &&
            command -v "${candidate}objcopy" >/dev/null 2>&1; then
            printf '%s' "${candidate}"
            return
        fi
    done
    print_error "No RV32-capable bare-metal RISC-V toolchain found"
    exit 1
}

verify_revision "${NUTTX_DIR}" "${NUTTX_REVISION}"
verify_revision "${NUTTX_APPS_DIR}" "${NUTTX_APPS_REVISION}"
NUTTX_DIR=$(cd -- "${NUTTX_DIR}" && pwd)
NUTTX_APPS_DIR=$(cd -- "${NUTTX_APPS_DIR}" && pwd)

cross_prefix=$(find_cross_prefix)
board_root="${NUTTX_DIR}/boards/risc-v/qemu-rv/rv-virt"
apps_relative=$(realpath --relative-to="${NUTTX_DIR}" "${NUTTX_APPS_DIR}")
config_dir=$(mktemp -d)
cleanup()
{
    if [ -L "${NUTTX_DIR}/Make.defs" ] &&
        [ "$(readlink "${NUTTX_DIR}/Make.defs")" = "${config_dir}/Make.defs" ]; then
        ln -sfn "${board_root}/scripts/Make.defs" "${NUTTX_DIR}/Make.defs"
    fi
    rm -rf -- "${config_dir}"
}
trap cleanup EXIT

if [ -e "${NUTTX_DIR}/.config" ]; then
    if [ ! -e "${NUTTX_DIR}/Make.defs" ]; then
        ln -sfn "${board_root}/scripts/Make.defs" "${NUTTX_DIR}/Make.defs"
    fi
    make -C "${NUTTX_DIR}" distclean
fi
"${NUTTX_DIR}/tools/process_config.sh" -I "${board_root}/configs" \
    -o "${config_dir}/defconfig" \
    "${RV32EMU_ROOT}/assets/system/configs/nuttx.config"
ln -s "${board_root}/scripts/Make.defs" "${config_dir}/Make.defs"
"${NUTTX_DIR}/tools/configure.sh" -l -a "${apps_relative}" "${config_dir}"
make -C "${NUTTX_DIR}" "${PARALLEL}" CROSSDEV="${cross_prefix}"

mkdir -p "${OUTPUT_DIR}"
cp "${NUTTX_DIR}/nuttx" "${OUTPUT_DIR}/nuttx"
"${cross_prefix}objcopy" -O binary "${NUTTX_DIR}/nuttx" \
    "${OUTPUT_DIR}/nuttx.bin"
cp "${NUTTX_DIR}/.config" "${OUTPUT_DIR}/nuttx.config"
cp "${config_dir}/defconfig" "${OUTPUT_DIR}/defconfig"
truncate -s 1M "${OUTPUT_DIR}/dummy.img"
printf '{\n  "nuttx": "%s",\n  "nuttx_apps": "%s"\n}\n' \
    "${NUTTX_REVISION}" "${NUTTX_APPS_REVISION}" \
    > "${OUTPUT_DIR}/metadata.json"

print_success "NuttX image written to ${OUTPUT_DIR}/nuttx.bin"
