#pragma once

#include <cstddef>
#include <cstdint>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Forward-declared handle that wraps a FAISS index instance.
 */
typedef struct FaissClientHandle FaissClientHandle;

typedef struct FaissClientInfo {
    std::size_t ntotal;
    int dim;
    int m;
    int ef_search;
    int metric_kind;
} FaissClientInfo;

/** Supported metric kinds for the FAISS client. */
typedef enum FaissMetricKind {
    FAISS_METRIC_L2 = 0,
    FAISS_METRIC_INNER_PRODUCT = 1,
} FaissMetricKind;

FaissClientHandle* faiss_client_create(
    int dim,
    int m,
    int ef_construction,
    int ef_search,
    FaissMetricKind metric_type);

void faiss_client_free(FaissClientHandle* handle);

/**
 * Adds `count` vectors (row-major, dim floats per vector) with explicit ids to the index.
 * Returns 0 on success, -1 on failure. Use faiss_client_get_last_error for details.
 */
int faiss_client_add(
    FaissClientHandle* handle,
    const float* vectors,
    const std::int64_t* ids,
    std::size_t count);

/**
 * Searches the index with a single query vector. `ids_out` receives `top_k` ids,
 * `distances_out` receives the corresponding distance values.
 */
int faiss_client_search(
    FaissClientHandle* handle,
    const float* query,
    int top_k,
    std::int64_t* ids_out,
    float* distances_out);

int faiss_client_reset(FaissClientHandle* handle);
int faiss_client_optimize(FaissClientHandle* handle);
int faiss_client_set_ef_search(FaissClientHandle* handle, int ef_search);
int faiss_client_save_index(FaissClientHandle* handle, const char* path);
int faiss_client_load_index(FaissClientHandle* handle, const char* path);
int faiss_client_get_info(FaissClientHandle* handle, FaissClientInfo* info_out);

/** Sets the global FAISS OpenMP thread pool size. */
void faiss_client_set_num_threads(int threads);

/** Returns a pointer to the last error string for the given handle (or nullptr). */
const char* faiss_client_get_last_error(FaissClientHandle* handle);

#ifdef __cplusplus
}
#endif
