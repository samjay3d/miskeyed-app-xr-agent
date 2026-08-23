cmake_minimum_required(VERSION 3.24)
project(miskeyed-app-xr-agent VERSION 0.1.0 LANGUAGES CXX)

include(CTest)
include(FetchContent)

set(MISKEYED_XR_AGENT_SOURCE "" CACHE PATH
    "Local miskeyed-xr-agent checkout (preferred while integrating)")
set(MISKEYED_XR_AGENT_GIT_TAG "ea1c6106c9e85b3d23491c403e47a6e4d6818fb0" CACHE STRING
    "Reviewed miskeyed-xr-agent integration revision")
set(KIT_ROOT "" CACHE PATH "Extracted Omniverse Kit SDK root")

if(MISKEYED_XR_AGENT_SOURCE)
  if(NOT EXISTS "${MISKEYED_XR_AGENT_SOURCE}/CMakeLists.txt")
    message(FATAL_ERROR "MISKEYED_XR_AGENT_SOURCE is not a core source checkout")
  endif()
  FetchContent_Declare(miskeyed_xr_agent SOURCE_DIR "${MISKEYED_XR_AGENT_SOURCE}")
else()
  FetchContent_Declare(miskeyed_xr_agent
    GIT_REPOSITORY https://github.com/samjay3d/miskeyed-xr-agent.git
    GIT_TAG "${MISKEYED_XR_AGENT_GIT_TAG}"
    GIT_SHALLOW FALSE)
endif()

set(MISKEYED_XR_BUILD_OPENXR OFF CACHE BOOL "" FORCE)
set(MISKEYED_XR_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(MISKEYED_XR_BUILD_PYTHON ON CACHE BOOL "" FORCE)
set(MISKEYED_XR_INSTALL_NATIVE_SDK OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING_SAVED "${BUILD_TESTING}")
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  FetchContent_Declare(pybind11
    URL https://github.com/pybind/pybind11/archive/refs/tags/v2.13.6.tar.gz
    URL_HASH SHA256=e08cb87f4773da97fa7b5f035de8763abc656d87d5773e62f6da0587d1f0ec20
    DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
  FetchContent_MakeAvailable(pybind11)
  # The core calls find_package even when a parent already provides pybind11.
  # Supply a tiny config bridge; the real imported/functions targets were
  # created above by pybind11's own CMake project.
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/cmake/pybind11")
  file(WRITE "${CMAKE_BINARY_DIR}/cmake/pybind11/pybind11Config.cmake"
       "set(pybind11_FOUND TRUE)\n")
  set(pybind11_DIR "${CMAKE_BINARY_DIR}/cmake/pybind11" CACHE PATH "" FORCE)
endif()
FetchContent_MakeAvailable(miskeyed_xr_agent)
set(BUILD_TESTING "${BUILD_TESTING_SAVED}" CACHE BOOL "" FORCE)

set(STAGE_DIR "${CMAKE_BINARY_DIR}/stage")
add_custom_target(stage ALL
  COMMAND "${CMAKE_COMMAND}" -E rm -rf "${STAGE_DIR}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${STAGE_DIR}/apps"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${STAGE_DIR}/exts"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${STAGE_DIR}/python/miskeyed/xr/agent"
  COMMAND "${CMAKE_COMMAND}" -E copy_directory "${CMAKE_SOURCE_DIR}/apps" "${STAGE_DIR}/apps"
  COMMAND "${CMAKE_COMMAND}" -E copy_directory "${CMAKE_SOURCE_DIR}/exts" "${STAGE_DIR}/exts"
  COMMAND "${CMAKE_COMMAND}" -E copy_directory
          "${miskeyed_xr_agent_SOURCE_DIR}/python/miskeyed/xr/agent"
          "${STAGE_DIR}/python/miskeyed/xr/agent"
  COMMAND "${CMAKE_COMMAND}" -E copy "$<TARGET_FILE:_spatial>"
          "${STAGE_DIR}/python/miskeyed/xr/agent/$<TARGET_FILE_NAME:_spatial>"
  DEPENDS _spatial
  COMMENT "Staging the Kit extension and reviewed core Python module")

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
    ENVIRONMENT "PYTHONPATH=${CMAKE_SOURCE_DIR}/exts/miskeyed.xr.adapter")
  add_test(NAME staged-core-smoke
    COMMAND "${Python_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tests/smoke_staged_core.py")
  if(WIN32)
    set(TEST_PATH_SEPARATOR ";")
  else()
    set(TEST_PATH_SEPARATOR ":")
  endif()
  set_tests_properties(staged-core-smoke PROPERTIES
    ENVIRONMENT
      "PYTHONPATH=${STAGE_DIR}/python${TEST_PATH_SEPARATOR}${CMAKE_SOURCE_DIR}/exts/miskeyed.xr.adapter")
endif()
