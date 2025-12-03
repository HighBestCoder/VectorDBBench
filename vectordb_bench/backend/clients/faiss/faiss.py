"""Local FAISS client wrapper for VectorDBBench."""

from __future__ import annotations

import logging
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np

from vectordb_bench.backend.filter import Filter, FilterOp

from ..api import MetricType, VectorDB
from .config import FaissIndexConfig

log = logging.getLogger(__name__)

# Ensure the faissclient package (native bindings + python wrapper) is importable.
_FAISSCLIENT_ROOT = Path(__file__).resolve().parents[5] / "faissclient"
if str(_FAISSCLIENT_ROOT) not in sys.path:
    sys.path.insert(0, str(_FAISSCLIENT_ROOT))

from faissclient import FaissNativeClient, MetricKind  # noqa: E402


class Faiss(VectorDB):
    name = "FAISS"
    supported_filter_types = [FilterOp.NonFilter]

    def __init__(
        self,
        dim: int,
        db_config: dict,
        db_case_config: FaissIndexConfig,
        collection_name: str = "local_faiss",
        drop_old: bool = False,
        with_scalar_labels: bool = False,
        **_: Any,
    ) -> None:
        self.dim = dim
        self.case_config = db_case_config
        self.collection_name = collection_name
        self.with_scalar_labels = with_scalar_labels

        self.faiss_root_override = db_config.get("faiss_root")
        self.client_library_override = db_config.get("client_library")
        self.batch_size = int(db_config.get("batch_size", 20000))
        self.num_threads = int(db_config.get("num_threads", 0))

        self._client: FaissNativeClient | None = None
        self._reset_on_start = drop_old

    def need_normalize_cosine(self) -> bool:
        return self.case_config.metric_type == MetricType.COSINE

    def _metric_kind(self) -> MetricKind:
        metric = self.case_config.metric_type
        if metric in (None, MetricType.L2):
            return MetricKind.L2
        if metric in (MetricType.COSINE, MetricType.IP):
            return MetricKind.INNER_PRODUCT
        return MetricKind.L2

    def _ensure_client(self) -> FaissNativeClient:
        if self._client is None:
            kind = self._metric_kind()
            self._client = FaissNativeClient(
                dim=self.dim,
                m=self.case_config.m,
                ef_construction=self.case_config.ef_construction,
                ef_search=self.case_config.ef_search,
                metric=kind,
                num_threads=self.num_threads,
                faiss_root=self.faiss_root_override,
                client_library=self.client_library_override,
            )
            if self._reset_on_start:
                self._client.reset()
                self._reset_on_start = False
        return self._client

    def _reset_index(self) -> None:
        if self._client:
            self._client.reset()

    @contextmanager
    def init(self) -> Generator[None, None, None]:
        self._ensure_client()
        yield

    def prepare_filter(self, filters: Filter):
        if filters.type is not FilterOp.NonFilter:
            msg = "Local FAISS client currently supports only non-filtered workloads"
            raise NotImplementedError(msg)

    def insert_embeddings(
        self,
        embeddings: list[list[float]]
        | np.ndarray,
        metadata: list[int]
        | np.ndarray,
        labels_data: list[str] | None = None,
        **_: Any,
    ) -> tuple[int, Exception | None]:
        del labels_data
        client = self._ensure_client()
        try:
            vectors = np.asarray(embeddings, dtype=np.float32)
            ids = np.asarray(metadata, dtype=np.int64)
            inserted = client.add(vectors, ids)
            return inserted, None
        except Exception as exc:  # noqa: BLE001
            log.warning(f"FAISS insert failed: {exc}")
            return 0, exc

    def search_embedding(self, query: list[float] | np.ndarray, k: int = 100, **_: Any) -> list[int]:
        client = self._ensure_client()
        try:
            ids, _ = client.search(np.asarray(query, dtype=np.float32), k)
            return ids.tolist()
        except Exception as exc:  # noqa: BLE001
            log.warning(f"FAISS search failed: {exc}")
            return []

    def optimize(self, data_size: int | None = None):  # noqa: ARG002
        client = self._ensure_client()
        # HNSW for FAISS is fully built during add(); keep the hook for interface parity.
        client.optimize()

    def __del__(self):  # noqa: D401
        if self._client:
            self._client.close()
            self._client = None
