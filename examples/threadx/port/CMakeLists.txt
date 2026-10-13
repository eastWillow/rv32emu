# Reuse upstream CPU support; startup.S supplies the board initialization.
set(PORT_DIR "${THREADX_DIR}/ports/risc-v32/gnu")
target_sources(threadx PRIVATE
    "${PORT_DIR}/src/tx_initialize_low_level.S"
    "${PORT_DIR}/src/tx_thread_context_restore.S"
    "${PORT_DIR}/src/tx_thread_context_save.S"
    "${PORT_DIR}/src/tx_thread_interrupt_control.S"
    "${PORT_DIR}/src/tx_thread_schedule.S"
    "${PORT_DIR}/src/tx_thread_stack_build.S"
    "${PORT_DIR}/src/tx_thread_system_return.S"
    "${PORT_DIR}/src/tx_timer_interrupt.S")
target_include_directories(threadx PUBLIC "${PORT_DIR}/inc")
