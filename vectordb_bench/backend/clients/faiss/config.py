"""Configuration objects for the local FAISS client."""

from pydantic import BaseModel

from ..api import DBCaseConfig, DBConfig, IndexType, MetricType


class FaissConfig(DBConfig):
    """Runtime configuration for the FAISS native client."""

    faiss_root: str | None = None
    client_library: str | None = None
    batch_size: int = 20000
    num_threads: int = 0
    index_dir: str | None = None

    def to_dict(self) -> dict:
        return {
            "faiss_root": self.faiss_root,
            "client_library": self.client_library,
            "batch_size": self.batch_size,
            "num_threads": self.num_threads,
            "index_dir": self.index_dir,
        }


class FaissIndexConfig(BaseModel, DBCaseConfig):
    metric_type: MetricType = MetricType.L2
    index_type: IndexType = IndexType.HNSW
    m: int = 16
    ef_construction: int = 200
    ef_search: int = 100

    def index_param(self) -> dict:
        return {"m": self.m, "ef_construction": self.ef_construction}

    def search_param(self) -> dict:
        return {"ef": self.ef_search}
