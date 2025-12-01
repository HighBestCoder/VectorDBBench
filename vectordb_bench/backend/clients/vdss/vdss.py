"""Wrapper around the VDSS vector database over VectorDB"""

import json
import logging
import os
import time
from contextlib import contextmanager
from typing import Any

import grpc

# Import generated gRPC code
import sys
from pathlib import Path

# Add vdeclient to path
vdeclient_path = Path(__file__).parent.parent.parent.parent.parent / "vdeclient"
sys.path.insert(0, str(vdeclient_path))

try:
    import vdss_service_pb2
    import vdss_service_pb2_grpc
    import vdss_types_pb2
except ImportError as e:
    raise ImportError(
        f"Failed to import VDSS gRPC modules. "
        f"Please generate them first: "
        f"cd vdeclient && python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. vdss_types.proto vdss_service.proto"
    ) from e

from vectordb_bench.backend.filter import Filter, FilterOp

from ..api import VectorDB
from .config import VDSSIndexConfig

log = logging.getLogger(__name__)


class VDSS(VectorDB):
    """VDSS vector database client"""
    
    supported_filter_types: list[FilterOp] = [
        FilterOp.NonFilter,
        FilterOp.NumGE,
        FilterOp.StrEqual,
    ]
    
    def __init__(
        self,
        dim: int,
        db_config: dict,
        db_case_config: VDSSIndexConfig,
        collection_name: str = "VDBBench",
        drop_old: bool = False,
        with_scalar_labels: bool = False,
        **kwargs,
    ):
        """Initialize wrapper around the VDSS vector database."""
        self.name = "VDSS"
        self.db_config = db_config
        self.case_config = db_case_config
        self.collection_name = collection_name
        self.dim = dim
        self.with_scalar_labels = with_scalar_labels
        
        # Get batch size from NUM_PER_BATCH environment variable, default to 100000
        self.batch_size = int(os.environ.get('NUM_PER_BATCH', 100000))
        log.info(f"VDSS batch_size set to: {self.batch_size}")
        
        self._primary_field = "pk"
        self._scalar_id_field = "id"
        self._scalar_label_field = "label"
        
        # gRPC connection settings
        self.grpc_host = db_config.get("grpc_host", "localhost")
        self.grpc_port = db_config.get("grpc_port", 50051)
        self.api_key = db_config.get("api_key")
        
        # Prepare filter condition if needed
        self.filter_json = None
        
        # Initialize collection
        self._init_collection(dim, drop_old)
    
    def _init_collection(self, dim: int, drop_old: bool):
        """Initialize collection with gRPC"""
        channel = grpc.insecure_channel(f'{self.grpc_host}:{self.grpc_port}')
        stub = vdss_service_pb2_grpc.VDSSServiceStub(channel)
        
        try:
            if drop_old:
                log.info(f"VDSS client drop_old collection: {self.collection_name}")
                # Try to delete existing collection
                try:
                    delete_req = vdss_service_pb2.DeleteCollectionRequest(
                        collection_name=self.collection_name
                    )
                    stub.DeleteCollection(delete_req)
                except Exception as e:
                    log.debug(f"Collection deletion failed (may not exist): {e}")
            
            # Create collection configuration with enum types
            config_json_dict = {
                "dtype": "float32",
                "metric_type": self.case_config.parse_metric_string(),
                "hnsw": {
                    "max_degree": self.case_config.m,
                    "ef_construction": self.case_config.ef_construction,
                }
            }
            
            # Create HnswConfig message
            hnsw_config = vdss_types_pb2.HnswConfig(
                m=self.case_config.m,
                ef_construct=self.case_config.ef_construction
            )
            
            config = vdss_types_pb2.CollectionConfig(
                index_driver=vdss_types_pb2.IndexDriver.FAISS,
                index_algorithm=self.case_config.parse_index_algorithm(),
                storage_type=vdss_types_pb2.StorageType.ZENDB,
                dimension=dim,
                distance_metric=self.case_config.parse_metric(),
                config_json=json.dumps(config_json_dict),
                hnsw_config=hnsw_config,
            )
            
            # Create collection
            create_req = vdss_service_pb2.CreateCollectionRequest(
                collection_name=self.collection_name,
                config=config
            )
            response = stub.CreateCollection(create_req)
            
            if response.status.code != 0:
                log.warning(f"Create collection returned code {response.status.code}: {response.status.message}")
            else:
                log.info(f"VDSS collection created: {self.collection_name}")
            
            # Open collection
            open_req = vdss_service_pb2.OpenCollectionRequest(
                collection_name=self.collection_name
            )
            open_response = stub.OpenCollection(open_req)
            
            if open_response.status.code != 0:
                log.error(f"Failed to open collection: {open_response.status.message}")
            
        except Exception as e:
            log.error(f"Failed to initialize VDSS collection: {e}")
            raise
        finally:
            channel.close()
    
    @contextmanager
    def init(self):
        """Create and destroy gRPC connection
        
        Examples:
            >>> with self.init():
            >>>     self.insert_embeddings()
            >>>     self.search_embedding()
        """
        # Create gRPC channel
        self.channel = grpc.insecure_channel(
            f'{self.grpc_host}:{self.grpc_port}',
            options=[
                ('grpc.max_send_message_length', 100 * 1024 * 1024),  # 100MB
                ('grpc.max_receive_message_length', 100 * 1024 * 1024),  # 100MB
            ]
        )
        self.stub = vdss_service_pb2_grpc.VDSSServiceStub(self.channel)
        
        yield
        
        # Close connection
        self.channel.close()
        self.stub = None
        self.channel = None
    
    def need_normalize_cosine(self) -> bool:
        """Whether this database needs to normalize dataset to support COSINE"""
        return False
    
    def prepare_filter(self, filters: Filter):
        """Prepare filter conditions for searching"""
        if filters.type == FilterOp.NonFilter:
            self.filter_json = None
            return
        
        # Prepare JSON filter based on filter type
        if filters.type == FilterOp.NumGE:
            # Assuming numeric filter on id field
            self.filter_json = json.dumps({
                "must": [{
                    "range": {
                        self._scalar_id_field: {
                            "gte": filters.lower_bound
                        }
                    }
                }]
            })
        elif filters.type == FilterOp.StrEqual:
            # String equality filter on label field
            self.filter_json = json.dumps({
                "must": [{
                    "match": {
                        self._scalar_label_field: filters.label
                    }
                }]
            })
        
        log.info(f"Prepared filter: {self.filter_json}")
    
    def insert_embeddings(
        self,
        embeddings: list[list[float]],
        metadata: list[int],
        labels_data: list[str] | None = None,
        **kwargs,
    ) -> tuple[int, Exception]:
        """Insert embeddings into VDSS via gRPC
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of IDs for the embeddings
            labels_data: Optional labels for filtering
            
        Returns:
            Tuple of (inserted_count, exception)
        """
        assert self.stub is not None, "Please call self.init() before insert_embeddings"
        assert len(embeddings) == len(metadata)
        
        insert_count = 0
        
        try:
            # Batch insert
            for batch_start in range(0, len(embeddings), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(embeddings))
                
                offsets = []
                vectors = []
                payloads = []
                
                for i in range(batch_start, batch_end):
                    offset = metadata[i]
                    vector_data = embeddings[i]
                    
                    # Create vector message
                    vector = vdss_types_pb2.Vector(
                        data=vector_data,
                        dimension=len(vector_data)
                    )
                    
                    # Create payload with metadata
                    payload_dict = {
                        self._scalar_id_field: int(offset)
                    }
                    if self.with_scalar_labels and labels_data:
                        payload_dict[self._scalar_label_field] = labels_data[i]
                    
                    payload = vdss_types_pb2.Payload(
                        json=json.dumps(payload_dict)
                    )
                    
                    offsets.append(offset)
                    vectors.append(vector)
                    payloads.append(payload)
                
                # Batch upsert request
                request = vdss_service_pb2.BatchUpsertRequest(
                    collection_name=self.collection_name,
                    offsets=offsets,
                    vectors=vectors,
                    payloads=payloads
                )
                
                response = self.stub.BatchUpsert(request)
                
                if response.status.code != 0:
                    log.error(f"Batch insert failed: {response.status.message}")
                    return insert_count, Exception(response.status.message)
                
                insert_count += len(offsets)
            
            return insert_count, None
            
        except Exception as e:
            log.error(f"Insert embeddings failed: {e}")
            return insert_count, e
    
    def search_embedding(
        self,
        query: list[float],
        k: int = 100,
    ) -> list[int]:
        """Search for k most similar embeddings via gRPC
        
        Args:
            query: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of IDs for the k most similar embeddings
        """
        assert self.stub is not None, "Please call self.init() before search_embedding"
        
        try:
            # Create query vector
            query_vector = vdss_types_pb2.Vector(
                data=query,
                dimension=len(query)
            )
            
            # Choose appropriate search method based on filter
            if self.filter_json:
                request = vdss_service_pb2.SearchFilteredRequest(
                    collection_name=self.collection_name,
                    query=query_vector,
                    top_k=k,
                    filter_json=self.filter_json
                )
                response = self.stub.SearchFiltered(request)
            else:
                request = vdss_service_pb2.SearchRequest(
                    collection_name=self.collection_name,
                    query=query_vector,
                    top_k=k
                )
                response = self.stub.Search(request)
            
            if response.status.code != 0:
                log.error(f"Search failed: {response.status.message}")
                return []
            
            # Extract offsets from results
            result_ids = [result.offset for result in response.results]
            return result_ids
            
        except Exception as e:
            log.error(f"Search embedding failed: {e}")
            return []
    
    def optimize(self, data_size: int | None = None):
        """Optimize the collection (rebuild index if needed)
        
        This will be called between insertion and search in performance cases.
        """
        assert self.stub is not None, "Please call self.init() before optimize"
        
        try:
            log.info(f"Starting VDSS collection optimization: {self.collection_name}")
            
            # Flush data to storage
            flush_req = vdss_service_pb2.FlushRequest(
                collection_name=self.collection_name
            )
            flush_response = self.stub.Flush(flush_req)
            
            if flush_response.status.code != 0:
                log.warning(f"Flush returned code {flush_response.status.code}: {flush_response.status.message}")
            
            # Rebuild index
            rebuild_req = vdss_service_pb2.RebuildIndexRequest(
                collection_name=self.collection_name
            )
            rebuild_response = self.stub.RebuildIndex(rebuild_req)
            
            if rebuild_response.status.code != 0:
                log.warning(f"Rebuild index returned code {rebuild_response.status.code}: {rebuild_response.status.message}")
            
            # Wait for optimization to complete
            time.sleep(2)
            
            # Get collection stats
            stats_req = vdss_service_pb2.GetStatsRequest(
                collection_name=self.collection_name
            )
            stats_response = self.stub.GetStats(stats_req)
            
            if stats_response.status.code == 0:
                stats = stats_response.stats
                log.info(
                    f"VDSS optimization complete - "
                    f"Total vectors: {stats.total_vectors}, "
                    f"Indexed: {stats.indexed_vectors}, "
                    f"Deleted: {stats.deleted_vectors}"
                )
            
        except Exception as e:
            log.warning(f"Optimize failed (non-critical): {e}")
