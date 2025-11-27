#!/usr/bin/env python3
"""Test VDSS connection and basic operations"""

import sys
import logging
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s: %(message)s'
)
log = logging.getLogger(__name__)

# VDSS Server Configuration
VDSS_HOST = "172.17.0.2"
VDSS_PORT = 50051

def test_imports():
    """Test that all VDSS modules can be imported"""
    log.info("=" * 60)
    log.info("Testing VDSS imports...")
    log.info("=" * 60)
    
    try:
        from vectordb_bench.backend.clients.vdss.config import VDSSConfig, VDSSIndexConfig
        log.info("✓ Config imports successful")
    except Exception as e:
        log.error(f"✗ Config import failed: {e}")
        return False
    
    try:
        from vectordb_bench.backend.clients.vdss.vdss import VDSS
        log.info("✓ VDSS client import successful")
    except Exception as e:
        log.error(f"✗ VDSS client import failed: {e}")
        return False
    
    try:
        from vectordb_bench.backend.clients import DB
        log.info("✓ DB enum import successful")
    except Exception as e:
        log.error(f"✗ DB enum import failed: {e}")
        return False
    
    return True


def test_grpc_connection():
    """Test gRPC connection to VDSS server"""
    log.info("\n" + "=" * 60)
    log.info("Testing gRPC connection...")
    log.info("=" * 60)
    
    try:
        import grpc
        sys.path.insert(0, '/builds/VectorDBBench/vdeclient')
        import vdss_service_pb2
        import vdss_service_pb2_grpc
        
        log.info(f"Connecting to VDSS at {VDSS_HOST}:{VDSS_PORT}...")
        
        channel = grpc.insecure_channel(f'{VDSS_HOST}:{VDSS_PORT}')
        stub = vdss_service_pb2_grpc.VDSSServiceStub(channel)
        
        # Try to get health check
        try:
            request = vdss_service_pb2.HealthCheckRequest()
            response = stub.HealthCheck(request, timeout=5)
            log.info(f"✓ gRPC connection successful!")
            log.info(f"  Status code: {response.status.code}")
            log.info(f"  VDSS version: {response.version}")
            log.info(f"  Uptime: {response.uptime_seconds} seconds")
        except grpc.RpcError as e:
            log.error(f"✗ gRPC call failed: {e}")
            return False
        finally:
            channel.close()
        
        return True
        
    except Exception as e:
        log.error(f"✗ gRPC connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vdss_operations():
    """Test basic VDSS operations"""
    log.info("\n" + "=" * 60)
    log.info("Testing VDSS operations...")
    log.info("=" * 60)
    
    try:
        from vectordb_bench.backend.clients.vdss.config import VDSSConfig, VDSSIndexConfig
        from vectordb_bench.backend.clients.vdss.vdss import VDSS
        from vectordb_bench.backend.clients.api import MetricType, IndexType
        
        # Create configuration
        log.info("Creating VDSS configuration...")
        config = VDSSConfig(
            db_label="test",
            grpc_host=VDSS_HOST,
            grpc_port=VDSS_PORT,
        )
        log.info(f"✓ Config created: {config.to_dict()}")
        
        index_config = VDSSIndexConfig(
            metric_type=MetricType.L2,
            index_type=IndexType.HNSW,
            m=16,
            ef_construction=200,
            ef_search=100,
            storage_type="zendb"
        )
        log.info(f"✓ Index config created")
        log.info(f"  - M: {index_config.m}")
        log.info(f"  - ef_construction: {index_config.ef_construction}")
        log.info(f"  - ef_search: {index_config.ef_search}")
        
        # Create VDSS client
        log.info("\nInitializing VDSS client...")
        dim = 128
        collection_name = "test_vectordb_bench"
        
        vdss = VDSS(
            dim=dim,
            db_config=config.to_dict(),
            db_case_config=index_config,
            collection_name=collection_name,
            drop_old=True,
        )
        log.info(f"✓ VDSS client initialized")
        log.info(f"  - Collection: {collection_name}")
        log.info(f"  - Dimension: {dim}")
        
        # Test insert
        log.info("\nTesting insert operations...")
        num_vectors = 100
        embeddings = np.random.rand(num_vectors, dim).tolist()
        metadata = list(range(num_vectors))
        
        with vdss.init():
            log.info(f"Inserting {num_vectors} vectors...")
            count, error = vdss.insert_embeddings(embeddings, metadata)
            
            if error:
                log.error(f"✗ Insert failed: {error}")
                return False
            
            log.info(f"✓ Inserted {count} vectors")
            
            # Optimize (flush and rebuild index)
            log.info("\nOptimizing collection...")
            vdss.optimize()
            log.info("✓ Optimization complete")
            
            # Test search
            log.info("\nTesting search operations...")
            query = embeddings[0]  # Use first vector as query
            k = 10
            
            results = vdss.search_embedding(query, k=k)
            
            if not results:
                log.error("✗ Search returned no results")
                return False
            
            log.info(f"✓ Search successful, found {len(results)} results")
            log.info(f"  - Top 5 IDs: {results[:5]}")
            
            # Verify the first result should be the query itself
            if results[0] == metadata[0]:
                log.info("✓ Top result matches query vector (as expected)")
            else:
                log.warning(f"⚠ Top result ({results[0]}) doesn't match query ID ({metadata[0]})")
        
        log.info("\n✓ All VDSS operations completed successfully!")
        return True
        
    except Exception as e:
        log.error(f"✗ VDSS operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    log.info("VDSS Integration Test")
    log.info(f"Target: {VDSS_HOST}:{VDSS_PORT}\n")
    
    success = True
    
    # Test 1: Imports
    if not test_imports():
        log.error("\n❌ Import tests failed!")
        return 1
    
    # Test 2: gRPC Connection
    if not test_grpc_connection():
        log.error("\n❌ gRPC connection tests failed!")
        return 1
    
    # Test 3: VDSS Operations
    if not test_vdss_operations():
        log.error("\n❌ VDSS operations tests failed!")
        return 1
    
    log.info("\n" + "=" * 60)
    log.info("🎉 All tests passed successfully!")
    log.info("=" * 60)
    log.info("\nYou can now use VDSS with vectordbbench CLI:")
    log.info(f"  vectordbbench vdsshnsw \\")
    log.info(f"    --grpc-host {VDSS_HOST} \\")
    log.info(f"    --grpc-port {VDSS_PORT} \\")
    log.info(f"    --case-type Performance768D100M \\")
    log.info(f"    --m 16 \\")
    log.info(f"    --ef-construction 200 \\")
    log.info(f"    --ef-search 100")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
