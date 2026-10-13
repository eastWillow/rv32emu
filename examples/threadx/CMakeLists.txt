cmake_minimum_required(VERSION 3.13)
project(rv32emu_threadx LANGUAGES C ASM)

get_filename_component(THREADX_DIR "${THREADX_DIR}" ABSOLUTE)
if(NOT EXISTS "${THREADX_DIR}/ports/risc-v32/gnu/inc/tx_port.h")
    message(FATAL_ERROR "THREADX_DIR must name a ThreadX checkout with the RV32 GNU port")
endif()
set(THREADX_ARCH "risc-v32")
set(THREADX_TOOLCHAIN "gnu")
set(THREADX_CUSTOM_PORT "${CMAKE_CURRENT_SOURCE_DIR}/port")
set(TX_USER_FILE "${CMAKE_CURRENT_SOURCE_DIR}/tx_user.h")
add_compile_options(-march=rv32ima_zicsr -mabi=ilp32 -O2 -g
    -ffreestanding -fno-builtin -ffunction-sections -fdata-sections)
include_directories("${CMAKE_CURRENT_SOURCE_DIR}/include")
add_subdirectory("${THREADX_DIR}" threadx EXCLUDE_FROM_ALL)
add_executable(threadx-demo.elf startup.S board.c demo.c)
target_link_libraries(threadx-demo.elf PRIVATE threadx gcc)
target_link_options(threadx-demo.elf PRIVATE -march=rv32ima_zicsr -mabi=ilp32
    -nostdlib -Wl,--gc-sections "-T${CMAKE_CURRENT_SOURCE_DIR}/link.ld"
    "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/threadx-demo.map")
set_property(TARGET threadx-demo.elf APPEND PROPERTY LINK_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/link.ld")
add_custom_command(TARGET threadx-demo.elf POST_BUILD
    COMMAND "${CMAKE_OBJCOPY}" -O binary $<TARGET_FILE:threadx-demo.elf>
        "${CMAKE_CURRENT_BINARY_DIR}/threadx-demo.bin")
