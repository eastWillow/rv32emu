# Build ThreadX outside its checkout; never download or modify its sources.
THREADX_DIR ?= $(abspath ../threadx)
THREADX_OUT := $(OUT)/threadx
THREADX_CROSS_COMPILE ?= riscv64-unknown-elf-
THREADX_JOBS ?= 2

.PHONY: threadx check-threadx
threadx:
	$(Q)cmake -S examples/threadx -B "$(THREADX_OUT)" \
	    -DCMAKE_TOOLCHAIN_FILE="$(abspath examples/threadx/toolchain.cmake)" \
	    -DTHREADX_DIR="$(abspath $(THREADX_DIR))" \
	    -DCROSS_COMPILE="$(THREADX_CROSS_COMPILE)"
	$(Q)cmake --build "$(THREADX_OUT)" --target threadx-demo.elf --parallel $(THREADX_JOBS)

ifeq ($(call has,SYSTEM)$(call has,JIT)$(call has,ELF_LOADER),100)
check-threadx: $(BIN) threadx
	$(Q)python3 tools/check-threadx.py "$(BIN)" "$(THREADX_OUT)/threadx-demo.bin"
else
check-threadx:
	$(Q)echo "check-threadx requires make baremetal_defconfig first" >&2
	$(Q)exit 1
endif
