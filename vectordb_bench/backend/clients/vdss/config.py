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
    storage_type: str = "zendb"  # "zendb", "mem", etc.
    
    # Additional driver-specific config (JSON format)
    config_json: str = "{}"
    
    def parse_storage_type(self) -> int:
        """Convert storage_type string to VDSS StorageType enum value"""
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
        sys.path.insert(0, str(vdeclient_path))
        import vdss_types_pb2
        
        storage_lower = self.storage_type.lower()
        if storage_lower == "zendb":
            return vdss_types_pb2.StorageType.ZENDB
        elif storage_lower == "mem" or storage_lower == "memory":
            return vdss_types_pb2.StorageType.MEM
        # Default to ZENDB
        return vdss_types_pb2.StorageType.ZENDB
    
    def parse_metric(self) -> int:
        """Convert MetricType to VDSS DistanceMetric enum value"""
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
        sys.path.insert(0, str(vdeclient_path))
        import vdss_types_pb2
        
        if self.metric_type == MetricType.L2:
            return vdss_types_pb2.DistanceMetric.EUCLIDEAN
        elif self.metric_type == MetricType.COSINE:
            return vdss_types_pb2.DistanceMetric.COSINE
        elif self.metric_type == MetricType.IP:
            return vdss_types_pb2.DistanceMetric.DOT
        return vdss_types_pb2.DistanceMetric.EUCLIDEAN
    
    def parse_metric_string(self) -> str:
        """Convert MetricType to metric string for config_json"""
        if self.metric_type == MetricType.L2:
            return "l2"
        elif self.metric_type == MetricType.COSINE:
            return "cosine"
        elif self.metric_type == MetricType.IP:
            return "dot"
        return "l2"
    
    def parse_index_algorithm(self) -> int:
        """Convert IndexType to VDSS IndexAlgorithm enum value"""
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path
        vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
        sys.path.insert(0, str(vdeclient_path))
        import vdss_types_pb2
        
        if self.index_type == IndexType.HNSW:
            return vdss_types_pb2.IndexAlgorithm.HNSW
        elif self.index_type in [IndexType.Hologres_HGraph]:
            return vdss_types_pb2.IndexAlgorithm.HNSW  # Only HNSW supported for now
        return vdss_types_pb2.IndexAlgorithm.HNSW
    
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
