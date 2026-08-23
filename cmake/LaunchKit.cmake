if(NOT EXISTS "${KIT_EXECUTABLE}")
  message(FATAL_ERROR
    "Kit executable not found at ${KIT_EXECUTABLE}. Reconfigure with "
    "-DKIT_ROOT=<extracted Kit SDK>. NVIDIA distributes Kit under terms that "
    "must be accepted by the developer, so this project cannot silently download it.")
endif()

execute_process(
  COMMAND "${KIT_EXECUTABLE}" "${STAGE_DIR}/apps/miskeyed.xr.kit"
          "--ext-folder" "${STAGE_DIR}/exts"
          "--/app/python/extraPaths/0=${STAGE_DIR}/python"
  COMMAND_ERROR_IS_FATAL ANY)

