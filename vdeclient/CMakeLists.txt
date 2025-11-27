# ============================================================================
# VDSS Protocol Buffers - protos/CMakeLists.txt
# ============================================================================
#
# Generate C++ code from .proto files for gRPC service
# Uses third-party gRPC installation (similar to FAISS pattern)
#
# ============================================================================

# Determine gRPC library path based on platform/architecture (same as FAISS)
if(WIN32)
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/windows-x64" CACHE PATH "gRPC library path")
    else()
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/windows-x86" CACHE PATH "gRPC library path")
    endif()
elseif(UNIX)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "^aarch64" OR CMAKE_SYSTEM_PROCESSOR MATCHES "^arm64")
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/linux-arm64" CACHE PATH "gRPC library path")
    elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^arm")
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/linux-arm32" CACHE PATH "gRPC library path")
    elseif(CMAKE_SIZEOF_VOID_P EQUAL 8)
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/linux-x64" CACHE PATH "gRPC library path")
    else()
        set(GRPCLIBS_PATH "${CMAKE_SOURCE_DIR}/third-party/grpc/linux-x86" CACHE PATH "gRPC library path")
    endif()
endif()

message(STATUS "gRPC library path: ${GRPCLIBS_PATH}")

# Set protobuf and gRPC paths
set(PROTOBUF_PROTOC_EXECUTABLE ${GRPCLIBS_PATH}/bin/protoc)
set(GRPC_CPP_PLUGIN ${GRPCLIBS_PATH}/bin/grpc_cpp_plugin)

# Verify tools exist
if(NOT EXISTS ${PROTOBUF_PROTOC_EXECUTABLE})
    message(FATAL_ERROR "protoc not found at ${PROTOBUF_PROTOC_EXECUTABLE}")
endif()
if(NOT EXISTS ${GRPC_CPP_PLUGIN})
    message(FATAL_ERROR "grpc_cpp_plugin not found at ${GRPC_CPP_PLUGIN}")
endif()

# Proto files
set(VDSS_PROTO_FILES
    ${CMAKE_CURRENT_SOURCE_DIR}/vdss_types.proto
    ${CMAKE_CURRENT_SOURCE_DIR}/vdss_service.proto
)

# Output directory for generated files (set as CACHE so it's visible to other subdirectories)
set(VDSS_PROTO_GENERATED_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated CACHE PATH "VDSS proto generated files directory")
file(MAKE_DIRECTORY ${VDSS_PROTO_GENERATED_DIR})

# Generate C++ sources from proto files
set(VDSS_PROTO_SRCS)
set(VDSS_PROTO_HDRS)
set(VDSS_GRPC_SRCS)
set(VDSS_GRPC_HDRS)

foreach(PROTO_FILE ${VDSS_PROTO_FILES})
    get_filename_component(PROTO_NAME ${PROTO_FILE} NAME_WE)
    
    list(APPEND VDSS_PROTO_SRCS ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.pb.cc)
    list(APPEND VDSS_PROTO_HDRS ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.pb.h)
    list(APPEND VDSS_GRPC_SRCS ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.grpc.pb.cc)
    list(APPEND VDSS_GRPC_HDRS ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.grpc.pb.h)
    
    add_custom_command(
        OUTPUT
            ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.pb.cc
            ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.pb.h
            ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.grpc.pb.cc
            ${VDSS_PROTO_GENERATED_DIR}/${PROTO_NAME}.grpc.pb.h
        COMMAND ${CMAKE_COMMAND} -E env LD_LIBRARY_PATH=${GRPCLIBS_PATH}/lib:$ENV{LD_LIBRARY_PATH}
            ${PROTOBUF_PROTOC_EXECUTABLE}
        ARGS
            --cpp_out=${VDSS_PROTO_GENERATED_DIR}
            --grpc_out=${VDSS_PROTO_GENERATED_DIR}
            --plugin=protoc-gen-grpc=${GRPC_CPP_PLUGIN}
            -I${CMAKE_CURRENT_SOURCE_DIR}
            ${PROTO_FILE}
        DEPENDS ${PROTO_FILE}
        COMMENT "Generating C++ code from ${PROTO_NAME}.proto"
        VERBATIM
    )
endforeach()

# Create static library with generated code
add_library(vdss_proto STATIC
    ${VDSS_PROTO_SRCS}
    ${VDSS_GRPC_SRCS}
)

# Include directories
target_include_directories(vdss_proto PUBLIC
    ${VDSS_PROTO_GENERATED_DIR}
    ${GRPCLIBS_PATH}/include
)

# Link gRPC and protobuf libraries (using full paths like FAISS)
target_link_libraries(vdss_proto PUBLIC
    ${GRPCLIBS_PATH}/lib/libprotobuf.so
    ${GRPCLIBS_PATH}/lib/libgrpc++.so
    ${GRPCLIBS_PATH}/lib/libgrpc.so
)

# Export variables to parent scope
set(VDSS_PROTO_GENERATED_DIR ${VDSS_PROTO_GENERATED_DIR} PARENT_SCOPE)
set(GRPCLIBS_PATH ${GRPCLIBS_PATH} PARENT_SCOPE)

message(STATUS "  Proto files: ${VDSS_PROTO_FILES}")
message(STATUS "  Generated directory: ${VDSS_PROTO_GENERATED_DIR}")
message(STATUS "  Protoc: ${PROTOBUF_PROTOC_EXECUTABLE}")
message(STATUS "  gRPC plugin: ${GRPC_CPP_PLUGIN}")
