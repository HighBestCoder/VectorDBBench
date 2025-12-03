"""Local FAISS client wrapper for VectorDBBench."""

from __future__ import annotations

import logging
import os
import re
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
        self.index_dir = Path(
            db_config.get("index_dir")
            or os.environ.get("FAISS_INDEX_DIR")
            or "/tmp/vectordb_bench/faiss_indexes",
        )
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self._index_file_path()

        self._client: FaissNativeClient | None = None
        self._reset_on_start = drop_old
        if drop_old and self.index_path.exists():
            try:
                self.index_path.unlink()
            except FileNotFoundError:
                pass
        self._dirty = False

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
                self._log_client_state("client-reset")
            elif self.index_path.exists():
                try:
                    self._client.load(self.index_path)
                    self._log_client_state("client-load-success")
                except Exception:  # noqa: BLE001
                    log.warning("Failed to load FAISS index from disk, starting empty", exc_info=True)
            self._log_client_state("client-created")
        return self._client

    def _reset_index(self) -> None:
        if self._client:
            log.warning("Resetting FAISS index on existing client")
            self._client.reset()
        else:
            log.warning("FAISS client not initialized; nothing to reset")

    @contextmanager
    def init(self) -> Generator[None, None, None]:
        self._ensure_client()
        try:
            yield
        finally:
            if self._dirty:
                self._log_client_state("client-before-save")
                self._persist_index()
                self._dirty = False
                self._log_client_state("client-after-save")

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
            self._dirty = True
            self._log_client_state("client-after-insert")
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
            log.warning("FAISS client closed")

    def _persist_index(self) -> None:
        client = self._client
        if client is None:
            log.warning("FAISS client not initialized; cannot persist index")
            return
        try:
            client.save(self.index_path)
            self._log_client_state("client-save")
            log.warning("FAISS index persisted to %s", self.index_path)
        except Exception:  # noqa: BLE001
            log.warning("Failed to persist FAISS index to disk", exc_info=True)

    def _index_file_path(self) -> Path:
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", self.collection_name)
        return self.index_dir / f"{safe_name}.faissindex"

    def _log_client_state(self, label: str) -> None:
        client = self._client
        if client is None:
            log.debug("[%s] client not initialized (path=%s)", label, self.index_path)
            return
        try:
            info = client.info()
        except Exception:  # noqa: BLE001
            log.warning("[%s] failed to get client info", label, exc_info=True)
            return
        log.info(
            "[%s] client_id=%s path=%s ntotal=%s dim=%s m=%s ef=%s metric=%s",
            label,
            hex(id(client)),
            self.index_path,
            info.get("ntotal"),
            info.get("dim"),
            info.get("m"),
            info.get("ef_search"),
            info.get("metric_kind"),
        )
