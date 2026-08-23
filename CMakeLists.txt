cmake_minimum_required(VERSION 3.24)
project(miskeyed-app-xr-agent VERSION 0.1.0 LANGUAGES NONE)

include(CTest)
find_package(Python COMPONENTS Interpreter REQUIRED)

set(KIT_ROOT "" CACHE PATH "Extracted Omniverse Kit SDK root")
set(STAGE_DIR "${CMAKE_BINARY_DIR}/stage")

add_custom_target(stage ALL
  COMMAND "${CMAKE_COMMAND}" -E rm -rf "${STAGE_DIR}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${STAGE_DIR}/apps"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${STAGE_DIR}/exts"
  COMMAND "${CMAKE_COMMAND}" -E copy_directory "${CMAKE_SOURCE_DIR}/apps" "${STAGE_DIR}/apps"
  COMMAND "${CMAKE_COMMAND}" -E copy_directory "${CMAKE_SOURCE_DIR}/exts" "${STAGE_DIR}/exts"
  COMMENT "Staging the pure-Python Kit application")

if(WIN32)
  set(KIT_EXECUTABLE "${KIT_ROOT}/kit/kit.exe")
else()
  set(KIT_EXECUTABLE "${KIT_ROOT}/kit/kit")
endif()

add_custom_target(launch
  COMMAND "${CMAKE_COMMAND}"
          "-DKIT_EXECUTABLE=${KIT_EXECUTABLE}"
          "-DSTAGE_DIR=${STAGE_DIR}"
          -P "${CMAKE_SOURCE_DIR}/cmake/LaunchKit.cmake"
  DEPENDS stage
  USES_TERMINAL)

if(BUILD_TESTING)
  add_test(NAME python-adapter-tests
    COMMAND "${Python_EXECUTABLE}" -m pytest -q "${CMAKE_SOURCE_DIR}/tests")
  set_tests_properties(python-adapter-tests PROPERTIES
    ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}/exts/miskeyed.kit.xr_agent")
  add_test(NAME released-core-smoke
    COMMAND "${Python_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/smoke_staged_core.py")
  set_tests_properties(released-core-smoke PROPERTIES
    ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}/exts/miskeyed.kit.xr_agent")
endif()
