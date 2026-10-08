#!/usr/bin/env bash

set -e -u -o pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
. "${SCRIPT_DIR}/common.sh"

defconfig=${1:-system_interpreter_defconfig}

make cleanconfig
make "${defconfig}"
make ${PARALLEL}
make check-system-interrupts
