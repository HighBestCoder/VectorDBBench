#!/usr/bin/env python3
"""Quick test to verify VDSS configuration"""

import sys
sys.path.insert(0, '/builds/VectorDBBench')

from vectordb_bench.backend.clients.vdss.config import VDSSConfig, VDSSIndexConfig
from vectordb_bench.backend.clients.vdss.vdss import VDSS
from vectordb_bench.backend.clients.api import MetricType, IndexType
import numpy as np

print("Testing VDSS Configuration...")

# Create config
config = VDSSConfig(
    db_label="test",
    grpc_host="172.17.0.2",
    grpc_port=50051,
)

index_config = VDSSIndexConfig(
    metric_type=MetricType.L2,
    index_type=IndexType.HNSW,
    m=16,
    ef_construction=200,
    ef_search=100,
    storage_type="zendb"
)

print(f"✓ Config created")
print(f"  - Index type: {index_config.parse_index_type()}")
print(f"  - Metric type: {index_config.parse_metric()}")
print(f"  - M: {index_config.m}")
print(f"  - ef_construction: {index_config.ef_construction}")

# Test VDSS client initialization
print("\nInitializing VDSS client...")
dim = 128
collection_name = "test_quick"

try:
    vdss = VDSS(
        dim=dim,
        db_config=config.to_dict(),
        db_case_config=index_config,
        collection_name=collection_name,
        drop_old=True,
    )
    print(f"✓ VDSS client initialized successfully")
    
    # Test insert
    print("\nTesting insert...")
    embeddings = np.random.rand(10, dim).tolist()
    metadata = list(range(10))
    
    with vdss.init():
        count, error = vdss.insert_embeddings(embeddings, metadata)
        if error:
            print(f"✗ Insert failed: {error}")
            sys.exit(1)
        
        print(f"✓ Inserted {count} vectors")
        
        # Test search
        print("\nTesting search...")
        query = embeddings[0]
        results = vdss.search_embedding(query, k=5)
        
        if not results:
            print("✗ Search returned no results")
            sys.exit(1)
        
        print(f"✓ Search returned {len(results)} results")
        print(f"  Top result ID: {results[0]}")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
