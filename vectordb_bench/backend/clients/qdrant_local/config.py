from pydantic import BaseModel, SecretStr

from ..api import DBCaseConfig, DBConfig, MetricType


class QdrantLocalConfig(DBConfig):
    url: SecretStr
    grpc_port: int | None = None  # Optional gRPC port
    prefer_grpc: bool = False  # Whether to prefer gRPC over HTTP

    def to_dict(self) -> dict:
        config = {
            "url": self.url.get_secret_value(),
        }
        if self.grpc_port is not None:
            config["grpc_port"] = self.grpc_port
        if self.prefer_grpc:
            config["prefer_grpc"] = self.prefer_grpc
        return config


class QdrantLocalIndexConfig(BaseModel, DBCaseConfig):
    metric_type: MetricType | None = None
    m: int
    ef_construct: int
    hnsw_ef: int | None = 0
    on_disk: bool | None = False

    def parse_metric(self) -> str:
        if self.metric_type == MetricType.L2:
            return "Euclid"

        if self.metric_type == MetricType.IP:
            return "Dot"

        return "Cosine"

    def index_param(self) -> dict:
        return {
            "distance": self.parse_metric(),
            "m": self.m,
            "ef_construct": self.ef_construct,
            "on_disk": self.on_disk,
        }

    def search_param(self) -> dict:
        search_params = {
            "exact": False,  # Force to use ANNs
        }

        if self.hnsw_ef != 0:
            search_params["hnsw_ef"] = self.hnsw_ef

        return search_params
