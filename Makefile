SIM ?= vcs
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/sync_fifo.v
TOPLEVEL = sync_fifo
COCOTB_TEST_MODULES = main

export VCS_COVERAGE = 1
export VCS_COV_SAVE_DISK = 1

COMPILE_ARGS += -full64 -debug_access+all +v2k
COMPILE_ARGS += -cm line+cond+fsm+tgl+branch
COMPILE_ARGS += -covgc

SIM_ARGS += -cm line+cond+fsm+tgl+branch
SIM_ARGS += -covgc

include $(shell cocotb-config --makefiles)/Makefile.sim

# 生成覆盖率
cov:
	cd sim_build && urg -full64 -dir c.vdb -report coverage

# Verdi
verdi:
	verdi -sv $(VERILOG_SOURCES) -ssf $(TOPLEVEL).fsdb &