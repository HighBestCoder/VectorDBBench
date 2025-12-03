from __future__ import annotations

import ctypes
import os
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_char_p,
    c_float,
    c_int,
    c_int64,
    c_size_t,
    c_void_p,
)
from enum import IntEnum
from pathlib import Path

import numpy as np


class MetricKind(IntEnum):
    L2 = 0
    INNER_PRODUCT = 1


class FaissNativeError(RuntimeError):
    pass


class _FaissClientInfo(Structure):
    _fields_ = [
        ("ntotal", c_size_t),
        ("dim", c_int),
        ("m", c_int),
        ("ef_search", c_int),
        ("metric_kind", c_int),
    ]


def _default_faiss_root() -> Path:
    env_override = os.environ.get("FAISS_ROOT")
    if env_override:
        return Path(env_override)

    data_candidate = Path("/data/third-party/faiss/linux-x64")
    if data_candidate.exists():
        return data_candidate

    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "third-party/faiss/linux-x64"


def _default_client_lib() -> Path:
    override = os.environ.get("FAISSCLIENT_LIB_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "lib/libfaissclient.so"


_LIB_CACHE: dict[tuple[str, str], ctypes.CDLL] = {}


def _load_native_library(
    faiss_root: str | os.PathLike[str] | None = None,
    client_library: str | os.PathLike[str] | None = None,
) -> ctypes.CDLL:
    root = Path(faiss_root) if faiss_root else _default_faiss_root()
    libfaiss = root / "lib/libfaiss.so"
    if not libfaiss.exists():
        msg = f"FAISS shared library not found at {libfaiss}. Set FAISS_ROOT to override."
        raise FaissNativeError(msg)

    lib_path = Path(client_library) if client_library else _default_client_lib()
    if not lib_path.exists():
        msg = f"faissclient shared library not found at {lib_path}. Build it under VectorDBBench/faissclient."
        raise FaissNativeError(msg)

    cache_key = (str(libfaiss.resolve()), str(lib_path.resolve()))
    if cache_key in _LIB_CACHE:
        return _LIB_CACHE[cache_key]

    mode = getattr(ctypes, "RTLD_GLOBAL", None)
    ctypes.CDLL(str(libfaiss), mode=mode) if mode is not None else ctypes.CDLL(str(libfaiss))

    lib = ctypes.CDLL(str(lib_path))
    lib.faiss_client_create.argtypes = [c_int, c_int, c_int, c_int, c_int]
    lib.faiss_client_create.restype = c_void_p

    lib.faiss_client_free.argtypes = [c_void_p]

    lib.faiss_client_add.argtypes = [c_void_p, POINTER(c_float), POINTER(c_int64), c_size_t]
    lib.faiss_client_add.restype = c_int

    lib.faiss_client_search.argtypes = [c_void_p, POINTER(c_float), c_int, POINTER(c_int64), POINTER(c_float)]
    lib.faiss_client_search.restype = c_int

    lib.faiss_client_reset.argtypes = [c_void_p]
    lib.faiss_client_reset.restype = c_int

    lib.faiss_client_optimize.argtypes = [c_void_p]
    lib.faiss_client_optimize.restype = c_int

    lib.faiss_client_set_ef_search.argtypes = [c_void_p, c_int]
    lib.faiss_client_set_ef_search.restype = c_int

    lib.faiss_client_set_num_threads.argtypes = [c_int]

    lib.faiss_client_save_index.argtypes = [c_void_p, c_char_p]
    lib.faiss_client_save_index.restype = c_int

    lib.faiss_client_load_index.argtypes = [c_void_p, c_char_p]
    lib.faiss_client_load_index.restype = c_int

    lib.faiss_client_get_last_error.argtypes = [c_void_p]
    lib.faiss_client_get_last_error.restype = c_char_p

    lib.faiss_client_get_info.argtypes = [c_void_p, POINTER(_FaissClientInfo)]
    lib.faiss_client_get_info.restype = c_int

    _LIB_CACHE[cache_key] = lib
    return lib


class FaissNativeClient:
    def __init__(
        self,
        dim: int,
        m: int,
        ef_construction: int,
        ef_search: int,
        metric: MetricKind,
        num_threads: int | None = None,
        faiss_root: str | os.PathLike[str] | None = None,
        client_library: str | os.PathLike[str] | None = None,
    ) -> None:
        self._lib = _load_native_library(faiss_root=faiss_root, client_library=client_library)
        self._handle = self._lib.faiss_client_create(dim, m, ef_construction, ef_search, int(metric))
        if not self._handle:
            raise FaissNativeError("Failed to create FAISS native client")
        if num_threads and num_threads > 0:
            self._lib.faiss_client_set_num_threads(num_threads)

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._lib.faiss_client_free(self._handle)
            self._handle = None

    def __del__(self) -> None:  # noqa: D401
        self.close()

    def reset(self) -> None:
        self._check(self._lib.faiss_client_reset(self._handle))

    def set_ef_search(self, ef_search: int) -> None:
        self._check(self._lib.faiss_client_set_ef_search(self._handle, ef_search))

    def optimize(self) -> None:
        self._check(self._lib.faiss_client_optimize(self._handle))

    def save(self, path: os.PathLike[str] | str) -> None:
        path_bytes = os.fsencode(path)
        self._check(self._lib.faiss_client_save_index(self._handle, path_bytes))

    def load(self, path: os.PathLike[str] | str) -> None:
        path_bytes = os.fsencode(path)
        self._check(self._lib.faiss_client_load_index(self._handle, path_bytes))

    def info(self) -> dict:
        info = _FaissClientInfo()
        self._check(self._lib.faiss_client_get_info(self._handle, byref(info)))
        return {
            "ntotal": int(info.ntotal),
            "dim": info.dim,
            "m": info.m,
            "ef_search": info.ef_search,
            "metric_kind": info.metric_kind,
        }

    def add(self, embeddings: np.ndarray, ids: np.ndarray) -> int:
        vecs = np.ascontiguousarray(embeddings, dtype=np.float32)
        id_buf = np.ascontiguousarray(ids, dtype=np.int64)
        if vecs.shape[0] != id_buf.shape[0]:
            msg = "Embeddings and ids must share the same leading dimension"
            raise FaissNativeError(msg)
        count = vecs.shape[0]
        self._check(
            self._lib.faiss_client_add(
                self._handle,
                vecs.ctypes.data_as(POINTER(c_float)),
                id_buf.ctypes.data_as(POINTER(c_int64)),
                count,
            ),
        )
        return count

    def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        q = np.ascontiguousarray(query, dtype=np.float32)
        ids = np.empty(top_k, dtype=np.int64)
        distances = np.empty(top_k, dtype=np.float32)
        self._check(
            self._lib.faiss_client_search(
                self._handle,
                q.ctypes.data_as(POINTER(c_float)),
                top_k,
                ids.ctypes.data_as(POINTER(c_int64)),
                distances.ctypes.data_as(POINTER(c_float)),
            ),
        )
        return ids, distances

    def _check(self, code: int) -> None:
        if code == 0:
            return
        err_ptr = self._lib.faiss_client_get_last_error(self._handle)
        message = err_ptr.decode() if err_ptr else "Unknown faissclient error"
        raise FaissNativeError(message)


__all__ = ["FaissNativeClient", "FaissNativeError", "MetricKind"]
