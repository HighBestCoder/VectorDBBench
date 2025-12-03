#include "faiss_client.h"

#include <faiss/IndexHNSW.h>
#include <faiss/IndexIDMap.h>
#include <faiss/index_io.h>
#include <omp.h>

#include <memory>
#include <new>
#include <string>

namespace {
struct FaissClientHandleImpl {
    std::unique_ptr<faiss::IndexIDMap> index;
    faiss::IndexHNSW* hnsw_index{nullptr};
    int dim{0};
    int m{0};
    int ef_search{0};
    FaissMetricKind metric_kind{FAISS_METRIC_L2};
    std::string last_error;
};

faiss::MetricType to_metric(FaissMetricKind kind) {
    switch (kind) {
        case FAISS_METRIC_INNER_PRODUCT:
            return faiss::MetricType::METRIC_INNER_PRODUCT;
        case FAISS_METRIC_L2:
        default:
            return faiss::MetricType::METRIC_L2;
    }
}

void store_error(FaissClientHandle* handle, const std::string& message) {
    if (handle != nullptr) {
        auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
        impl->last_error = message;
    }
}
}  // namespace

extern "C" FaissClientHandle* faiss_client_create(
    int dim,
    int m,
    int ef_construction,
    int ef_search,
    FaissMetricKind metric_type) {
    try {
        auto impl = std::make_unique<FaissClientHandleImpl>();
        impl->dim = dim;
        impl->m = m;
        impl->ef_search = ef_search;
        impl->metric_kind = metric_type;

        auto* hnsw = new faiss::IndexHNSWFlat(dim, m, to_metric(metric_type));
        hnsw->hnsw.efConstruction = ef_construction;
        hnsw->hnsw.efSearch = ef_search;
        hnsw->metric_type = to_metric(metric_type);

        auto index = std::make_unique<faiss::IndexIDMap>(hnsw);
        index->own_fields = true;

        impl->hnsw_index = dynamic_cast<faiss::IndexHNSW*>(index->index);
        impl->index = std::move(index);
        return reinterpret_cast<FaissClientHandle*>(impl.release());
    } catch (const std::bad_alloc&) {
        return nullptr;
    } catch (const std::exception&) {
        return nullptr;
    }
}

extern "C" void faiss_client_free(FaissClientHandle* handle) {
    if (handle == nullptr) {
        return;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    delete impl;
}

extern "C" int faiss_client_add(
    FaissClientHandle* handle,
    const float* vectors,
    const std::int64_t* ids,
    std::size_t count) {
    if (handle == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        impl->index->add_with_ids(count, vectors, ids);
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_search(
    FaissClientHandle* handle,
    const float* query,
    int top_k,
    std::int64_t* ids_out,
    float* distances_out) {
    if (handle == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        impl->index->search(1, query, top_k, distances_out, ids_out);
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_reset(FaissClientHandle* handle) {
    if (handle == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        impl->index->reset();
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_optimize(FaissClientHandle* handle) {
    if (handle == nullptr) {
        return -1;
    }
    // Nothing to do yet for HNSW, but keep the hook for parity with VDSS client.
    return 0;
}

extern "C" int faiss_client_save_index(FaissClientHandle* handle, const char* path) {
    if (handle == nullptr || path == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        faiss::write_index(impl->index.get(), path);
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_load_index(FaissClientHandle* handle, const char* path) {
    if (handle == nullptr || path == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        std::unique_ptr<faiss::Index> loaded(faiss::read_index(path));
        faiss::IndexIDMap* id_map = dynamic_cast<faiss::IndexIDMap*>(loaded.get());
        std::unique_ptr<faiss::IndexIDMap> new_index;
        if (id_map != nullptr) {
            loaded.release();
            new_index.reset(id_map);
        } else {
            auto tmp = std::make_unique<faiss::IndexIDMap>(loaded.release());
            tmp->own_fields = true;
            new_index = std::move(tmp);
        }
        impl->hnsw_index = dynamic_cast<faiss::IndexHNSW*>(new_index->index);
        if (auto* hnsw = impl->hnsw_index) {
            impl->ef_search = hnsw->hnsw.efSearch;
            impl->m = hnsw->hnsw.nb_neighbors(0);
        }
        impl->index = std::move(new_index);
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_set_ef_search(FaissClientHandle* handle, int ef_search) {
    if (handle == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    if (impl->hnsw_index == nullptr) {
        return -1;
    }
    try {
        impl->hnsw_index->hnsw.efSearch = ef_search;
        impl->ef_search = ef_search;
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" int faiss_client_get_info(FaissClientHandle* handle, FaissClientInfo* info_out) {
    if (handle == nullptr || info_out == nullptr) {
        return -1;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    try {
        info_out->dim = impl->dim;
        info_out->m = impl->m;
        info_out->ef_search = impl->hnsw_index ? impl->hnsw_index->hnsw.efSearch : impl->ef_search;
        info_out->metric_kind = static_cast<int>(impl->metric_kind);
        info_out->ntotal = impl->index ? static_cast<std::size_t>(impl->index->ntotal) : 0;
        return 0;
    } catch (const std::exception& ex) {
        store_error(handle, ex.what());
        return -1;
    }
}

extern "C" void faiss_client_set_num_threads(int threads) {
    if (threads > 0) {
        omp_set_num_threads(threads);
    }
}

extern "C" const char* faiss_client_get_last_error(FaissClientHandle* handle) {
    if (handle == nullptr) {
        return nullptr;
    }
    auto* impl = reinterpret_cast<FaissClientHandleImpl*>(handle);
    return impl->last_error.c_str();
}
