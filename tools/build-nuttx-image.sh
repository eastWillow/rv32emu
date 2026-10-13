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

verify_clean_source()
{
    local directory=$1
    local changes
    changes=$(git -C "${directory}" status --porcelain=v1 \
        --untracked-files=all --ignore-submodules=none)
    if [ -n "${changes}" ]; then
        print_error "${directory} has local source changes; refusing to build"
        printf '%s\n' "${changes}" >&2
        exit 1
    fi
}

checkout_revision()
{
    local source=$1
    local revision=$2
    local destination=$3

    if ! git clone --shared --no-checkout -- "${source}" "${destination}"; then
        print_error "Failed to clone source repository ${source}"
        exit 1
    fi
    if ! git -C "${destination}" checkout --detach "${revision}"; then
        print_error "Failed to check out requested revision ${revision}"
        exit 1
    fi
    verify_revision "${destination}" "${revision}"
    if ! git -C "${destination}" submodule update --init --recursive; then
        print_error "Failed to initialize pinned submodules in ${destination}"
        exit 1
    fi
    verify_clean_source "${destination}"
}

find_cross_prefix()
{
    local candidate
    for candidate in "${CROSS_COMPILE:-}" riscv-none-elf- riscv64-unknown-elf-; do
        [ -n "${candidate}" ] || continue
        if command -v "${candidate}gcc" > /dev/null 2>&1 \
            && command -v "${candidate}objcopy" > /dev/null 2>&1; then
            printf '%s' "${candidate}"
            return
        fi
    done
    print_error "No RV32-capable bare-metal RISC-V toolchain found"
    exit 1
}

path_is_within()
{
    local path=${1%/}
    local root=${2%/}
    [ -n "${root}" ] || root=/
    if [ "${root}" = / ]; then
        [[ "${path}/" == /* ]]
    else
        [[ "${path}" = "${root}" || "${path}" = "${root}/"* ]]
    fi
}

verify_revision "${NUTTX_DIR}" "${NUTTX_REVISION}"
verify_revision "${NUTTX_APPS_DIR}" "${NUTTX_APPS_REVISION}"
# Git status still reports tracked changes but omits ignored untracked files.
# Checkout from Git below so ignored files cannot enter the build inputs.
verify_clean_source "${NUTTX_DIR}"
verify_clean_source "${NUTTX_APPS_DIR}"
NUTTX_DIR=$(cd -- "${NUTTX_DIR}" && pwd -P)
NUTTX_APPS_DIR=$(cd -- "${NUTTX_APPS_DIR}" && pwd -P)
NUTTX_SOURCE_DIR=${NUTTX_DIR}
NUTTX_APPS_SOURCE_DIR=${NUTTX_APPS_DIR}

cross_prefix=$(find_cross_prefix)
build_root=$(mktemp -d)
build_root=$(cd -- "${build_root}" && pwd -P)
config_dir="${build_root}/config"
mkdir -p -- "${config_dir}"
NUTTX_BUILD_DIR="${build_root}/nuttx"
NUTTX_APPS_BUILD_DIR="${build_root}/nuttx-apps"
cleanup()
{
    rm -rf -- "${build_root}"
}
trap cleanup EXIT

output_dir=$(realpath -m -- "${OUTPUT_DIR}")
for source_dir in "${NUTTX_SOURCE_DIR}" "${NUTTX_APPS_SOURCE_DIR}"; do
    if path_is_within "${output_dir}" "${source_dir}" \
        || path_is_within "${source_dir}" "${output_dir}"; then
        print_error "OUTPUT_DIR must not overlap source checkout ${source_dir}"
        exit 1
    fi
done
if path_is_within "${output_dir}" "${build_root}"; then
    print_error "OUTPUT_DIR must be outside the temporary build tree"
    exit 1
fi

checkout_revision "${NUTTX_SOURCE_DIR}" "${NUTTX_REVISION}" "${NUTTX_BUILD_DIR}"
checkout_revision "${NUTTX_APPS_SOURCE_DIR}" "${NUTTX_APPS_REVISION}" \
    "${NUTTX_APPS_BUILD_DIR}"
NUTTX_DIR=${NUTTX_BUILD_DIR}
NUTTX_APPS_DIR=${NUTTX_APPS_BUILD_DIR}
board_root="${NUTTX_DIR}/boards/risc-v/qemu-rv/rv-virt"
apps_relative=$(realpath --relative-to="${NUTTX_DIR}" "${NUTTX_APPS_DIR}")

"${NUTTX_DIR}/tools/process_config.sh" -I "${board_root}/configs" \
    -o "${config_dir}/defconfig" \
    "${RV32EMU_ROOT}/assets/system/configs/nuttx.config"
ln -s "${board_root}/scripts/Make.defs" "${config_dir}/Make.defs"
"${NUTTX_DIR}/tools/configure.sh" -l -a "${apps_relative}" "${config_dir}"
make -C "${NUTTX_DIR}" "${PARALLEL}" CROSSDEV="${cross_prefix}"

mkdir -p "${output_dir}"
cp "${NUTTX_DIR}/nuttx" "${output_dir}/nuttx"
"${cross_prefix}objcopy" -O binary "${NUTTX_DIR}/nuttx" \
    "${output_dir}/nuttx.bin"
cp "${NUTTX_DIR}/.config" "${output_dir}/nuttx.config"
cp "${config_dir}/defconfig" "${output_dir}/defconfig"
truncate -s 1M "${output_dir}/dummy.img"
printf '{\n  "nuttx": "%s",\n  "nuttx_apps": "%s"\n}\n' \
    "${NUTTX_REVISION}" "${NUTTX_APPS_REVISION}" \
    > "${output_dir}/metadata.json"

print_success "NuttX image written to ${output_dir}/nuttx.bin"
