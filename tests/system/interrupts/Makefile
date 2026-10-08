ROOT ?= ../../..
OUT ?= $(ROOT)/build/system-interrupts
CROSS_COMPILE ?= riscv64-unknown-elf-
EMULATOR ?= $(ROOT)/build/rv32emu

PROGRAMS := uart-iir csr-pending timer-chain
ELFS := $(addprefix $(OUT)/,$(addsuffix .elf,$(PROGRAMS)))
BINS := $(ELFS:.elf=.bin)

.PHONY: all check clean

all: $(BINS)

$(OUT):
	mkdir -p $@

$(OUT)/%.elf: %.S | $(OUT)
	$(CROSS_COMPILE)gcc -march=rv32imac_zicsr -mabi=ilp32 -nostdlib \
		-static -Wl,-Ttext=0,-e,_start,--no-relax -o $@ $<

$(OUT)/%.bin: $(OUT)/%.elf
	$(CROSS_COMPILE)objcopy -O binary $< $@

check: all
	python3 run.py --emulator $(EMULATOR) $(BINS)

clean:
	rm -rf $(OUT)
