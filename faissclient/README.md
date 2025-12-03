# Local FAISS Client

This module provides a minimal native wrapper around the FAISS HNSW index so that VectorDBBench can benchmark a
fully local setup without any network hops. The wrapper is compiled into `libfaissclient.so` and accessed from Python
through `ctypes`.

## Prerequisites

- GCC/Clang toolchain with CMake >= 3.16
- The prebuilt FAISS package located under `/src/third-party/faiss/linux-x64` (default path used by the build)

If FAISS lives somewhere else, set the `FAISS_ROOT` CMake cache variable to the desired directory that contains the
`include/` and `lib/` folders.

## Build

```bash
cd /src/VectorDBBench/faissclient
cmake -S . -B build -DFAISS_ROOT=/src/third-party/faiss/linux-x64
cmake --build build --config Release
```

The compiled shared library will be placed inside `VectorDBBench/faissclient/lib/libfaissclient.so`. The Python wrapper
loads the library from that location by default. To override the path, set `FAISSCLIENT_LIB_PATH` before running
`vectordbbench`.
