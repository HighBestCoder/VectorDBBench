# VDSS Protocol Buffers

This directory contains Protocol Buffer definitions for the Vector Search Service (VDSS) gRPC API.

## Files

- **vdss_types.proto**: Common data types (Vector, Document, SearchResult, etc.)
- **vdss_service.proto**: gRPC service definition with RPC methods

## Code Generation

The proto files are automatically compiled to C++ code during the CMake build process.

Generated files are placed in: `build/comp/vdss/protos/generated/`

### Generated Files

- `vdss_types.pb.h/cc` - Protobuf message classes
- `vdss_types.grpc.pb.h/cc` - gRPC service stubs
- `vdss_service.pb.h/cc` - Protobuf message classes
- `vdss_service.grpc.pb.h/cc` - gRPC service stubs

## Usage

### In C++ Code

```cpp
#include "vdss_service.grpc.pb.h"
#include "vdss_types.pb.h"

// Create a search request
vdss::SearchRequest request;
request.set_collection_name("my_collection");
request.set_top_k(10);

auto* query_vector = request.mutable_query_vector();
query_vector->add_values(0.1f);
query_vector->add_values(0.2f);
// ...
```

## Manual Compilation (for reference)

If you need to manually compile the proto files:

```bash
protoc --cpp_out=. --grpc_out=. \
  --plugin=protoc-gen-grpc=$(which grpc_cpp_plugin) \
  vdss_types.proto vdss_service.proto
```
