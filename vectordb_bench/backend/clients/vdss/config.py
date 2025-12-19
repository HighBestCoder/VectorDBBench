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
    
    # HNSW parameters
    m: int = 16
    ef_construction: int = 200
    ef_search: int = 100
    
    # Storage configuration - use enum value
    storage_type: str = "ZENDB"  # "ZENDB", "MEM", "BTRIEVE_SPACE"
    
    # Index driver and algorithm
    index_driver: str = "FAISS"  # Currently only FAISS is supported
    index_algorithm: str = "HNSW"  # Currently only HNSW is supported
    
    def parse_metric(self) -> int:
        """Convert MetricType to VDSS DistanceMetric enum value"""
        # Import at runtime to avoid circular dependency
        import sys
        from pathlib import Path
        vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
        if str(vdeclient_path) not in sys.path:
            sys.path.insert(0, str(vdeclient_path))
        import vdss_types_pb2
        
        if self.metric_type == MetricType.L2:
            return vdss_types_pb2.EUCLIDEAN
        elif self.metric_type == MetricType.COSINE:
            return vdss_types_pb2.COSINE
        elif self.metric_type == MetricType.IP:
            return vdss_types_pb2.DOT
        return vdss_types_pb2.COSINE
    
    def parse_storage_type(self) -> int:
        """Convert storage type string to enum value"""
        import sys
        from pathlib import Path
        vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
        if str(vdeclient_path) not in sys.path:
            sys.path.insert(0, str(vdeclient_path))
        import vdss_types_pb2
        
        if self.storage_type.upper() == "ZENDB":
            return vdss_types_pb2.ZENDB
        elif self.storage_type.upper() == "MEM":
            return vdss_types_pb2.MEM
        elif self.storage_type.upper() == "BTRIEVE_SPACE":
            return vdss_types_pb2.BTRIEVE_SPACE
        return vdss_types_pb2.ZENDB
    
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
