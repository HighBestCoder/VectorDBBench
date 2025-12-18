"""Configuration for VDSS vector database"""

from pydantic import BaseModel, SecretStr

from ..api import DBCaseConfig, DBConfig, IndexType, MetricType


class VDSSConfig(DBConfig):
    """VDSS database connection configuration"""
    
    grpc_host: str = "localhost"
    grpc_port: int = 50051
    # Optional authentication
    api_key: SecretStr | None = None
    
    def to_dict(self) -> dict:
        config = {
            "grpc_host": self.grpc_host,
            "grpc_port": self.grpc_port,
        }
        if self.api_key:
            config["api_key"] = self.api_key.get_secret_value()
        return config


class VDSSIndexConfig(BaseModel, DBCaseConfig):
    """VDSS index configuration"""
    
    metric_type: MetricType | None = None
    index_type: IndexType = IndexType.HNSW
    
    # HNSW/HGraph parameters
    m: int = 16
    ef_construction: int = 200
    ef_search: int = 100
    
    # Storage configuration
    storage_type: str = "zendb"  # "zendb", "lmdb", etc.
    
    # Additional driver-specific config (JSON format)
    config_json: str = "{}"
    
    def parse_metric(self) -> str:
        """Convert MetricType to VDSS distance metric string"""
        if self.metric_type == MetricType.L2:
            return "euclidean"
        elif self.metric_type == MetricType.COSINE:
            return "cosine"
        elif self.metric_type == MetricType.IP:
            return "dot"
        return "cosine"
    
    def parse_index_type(self) -> str:
        """Convert IndexType to VDSS index type string"""
        if self.index_type == IndexType.HNSW:
            return "vsag_hnsw"
        elif self.index_type in [IndexType.Hologres_HGraph]:
            return "vsag_hgraph"
        return "vsag_hnsw"
    
    def index_param(self) -> dict:
        """Return index building parameters"""
        return {
            "m": self.m,
            "ef_construction": self.ef_construction,
        }
    
    def search_param(self) -> dict:
        """Return search parameters"""
        return {
            "ef": self.ef_search,
        }
