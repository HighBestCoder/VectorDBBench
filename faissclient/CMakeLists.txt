cmake_minimum_required(VERSION 3.16)
project(faissclient LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(FAISS_ROOT "" CACHE PATH "Path to the FAISS installation root (with include/ and lib/)")
if(NOT FAISS_ROOT)
    get_filename_component(REPO_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." REALPATH)
    set(FAISS_ROOT "${REPO_ROOT}/third-party/faiss/linux-x64" CACHE PATH "" FORCE)
endif()

if(NOT EXISTS "${FAISS_ROOT}/include" OR NOT EXISTS "${FAISS_ROOT}/lib")
    message(FATAL_ERROR "Unable to locate FAISS headers or libraries under ${FAISS_ROOT}. Set FAISS_ROOT explicitly.")
endif()

find_package(OpenMP REQUIRED)

add_library(faissclient SHARED
    src/faiss_client.cpp
)

target_include_directories(faissclient
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${FAISS_ROOT}/include
)

target_link_directories(faissclient PRIVATE ${FAISS_ROOT}/lib)

target_link_libraries(faissclient
    PRIVATE
        faiss
        OpenMP::OpenMP_CXX
)

set_target_properties(faissclient PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/lib
)

if(CMAKE_SYSTEM_NAME MATCHES "Linux")
    target_link_libraries(faissclient PRIVATE pthread)
endif()
