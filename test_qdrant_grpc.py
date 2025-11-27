#!/usr/bin/env python3
"""
Qdrant gRPC Client Test

Test Qdrant with same scale as VDSS test:
- Dataset: Performance1536D50K (50K vectors, 1536 dimensions)
- Index: HNSW (m=16, ef_construction=200, ef_search=100)
"""

import sys
import time
import random
import math
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, VectorParams, HnswConfigDiff,
        PointStruct, SearchRequest
    )
except ImportError:
    print("❌ qdrant-client not installed")
    print("Install with: pip install qdrant-client")
    sys.exit(1)

# Configuration matching VDSS test
QDRANT_HOST = "172.17.0.4"
QDRANT_GRPC_PORT = 6334
COLLECTION_NAME = "test_performance_1536d_50k"

# Test parameters (same as VDSS)
VECTOR_DIM = 1536
NUM_VECTORS = 50000  # 50K vectors
TOP_K = 100
BATCH_SIZE = 1000

# HNSW parameters (same as VDSS)
M = 16
EF_CONSTRUCTION = 200
EF_SEARCH = 100


def generate_random_vector(dim):
    """Generate a random normalized vector"""
    vec = [random.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-6:
        vec = [x / norm for x in vec]
    return vec


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def format_time(seconds):
    """Format seconds to human readable"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        return f"{seconds/60:.2f}m"
    else:
        return f"{seconds/3600:.2f}h"


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║        Qdrant gRPC Performance Test                             ║")
    print("║        Matching VDSS Test Scale (50K vectors, 1536 dim)         ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    print(f"\n📋 Test Configuration:")
    print(f"   - Qdrant Host: {QDRANT_HOST}")
    print(f"   - gRPC Port: {QDRANT_GRPC_PORT}")
    print(f"   - Vector Dimension: {VECTOR_DIM}")
    print(f"   - Number of Vectors: {NUM_VECTORS:,}")
    print(f"   - Top-K: {TOP_K}")
    print(f"   - HNSW M: {M}")
    print(f"   - HNSW ef_construction: {EF_CONSTRUCTION}")
    print(f"   - HNSW ef (search): {EF_SEARCH}")
    print(f"   - Batch Size: {BATCH_SIZE}")
    
    # Connect to Qdrant
    print_header("Connecting to Qdrant")
    
    try:
        client = QdrantClient(
            host=QDRANT_HOST,
            grpc_port=QDRANT_GRPC_PORT,
            prefer_grpc=True,
            timeout=300
        )
        
        # Health check
        collections = client.get_collections()
        print(f"✓ Connected to Qdrant via gRPC")
        print(f"  Existing collections: {len(collections.collections)}")
        
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print(f"\nMake sure Qdrant is running:")
        print(f"  docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return 1
    
    # Delete collection if exists
    print_header("Preparing Collection")
    
    try:
        client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✓ Deleted existing collection: {COLLECTION_NAME}")
    except Exception:
        print(f"  Collection '{COLLECTION_NAME}' does not exist (OK)")
    
    # Create collection with HNSW index
    print(f"\nCreating collection with HNSW index...")
    start_time = time.time()
    
    try:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_DIM,
                distance=Distance.COSINE,  # Same as VDSS test
            ),
            hnsw_config=HnswConfigDiff(
                m=M,
                ef_construct=EF_CONSTRUCTION,
            ),
        )
        
        create_time = time.time() - start_time
        print(f"✓ Collection created successfully ({create_time:.2f}s)")
        print(f"  Note: ef parameter ({EF_SEARCH}) will be set per search request")
        
    except Exception as e:
        print(f"❌ Failed to create collection: {e}")
        return 1
    
    # Insert vectors
    print_header("Inserting Vectors")
    
    print(f"Generating and inserting {NUM_VECTORS:,} vectors...")
    print(f"  (This will take several minutes...)")
    
    insert_start = time.time()
    total_inserted = 0
    
    try:
        for batch_start in range(0, NUM_VECTORS, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, NUM_VECTORS)
            batch_size = batch_end - batch_start
            
            # Generate batch of points
            points = []
            for i in range(batch_start, batch_end):
                vector = generate_random_vector(VECTOR_DIM)
                point = PointStruct(
                    id=i,
                    vector=vector,
                    payload={
                        "id": i,
                        "category": "even" if i % 2 == 0 else "odd",
                        "value": i * 100
                    }
                )
                points.append(point)
            
            # Upload batch
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                wait=False  # Async for faster insertion
            )
            
            total_inserted += batch_size
            
            # Progress update every 5K vectors
            if total_inserted % 5000 == 0:
                elapsed = time.time() - insert_start
                rate = total_inserted / elapsed
                remaining = (NUM_VECTORS - total_inserted) / rate
                print(f"   ✓ Inserted {total_inserted:,}/{NUM_VECTORS:,} vectors "
                      f"({total_inserted*100//NUM_VECTORS}%) - "
                      f"Rate: {rate:.0f} vec/s - "
                      f"ETA: {format_time(remaining)}")
        
        # Wait for all operations to complete
        print(f"\n  Waiting for indexing to complete...")
        time.sleep(5)
        
        insert_time = time.time() - insert_start
        insert_rate = NUM_VECTORS / insert_time
        
        print(f"\n✓ Successfully inserted {total_inserted:,} vectors")
        print(f"  Total time: {format_time(insert_time)}")
        print(f"  Average rate: {insert_rate:.0f} vectors/sec")
        
    except Exception as e:
        print(f"\n❌ Insertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Get collection info
    print_header("Collection Statistics")
    
    try:
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"  Vectors count: {collection_info.vectors_count:,}")
        print(f"  Points count: {collection_info.points_count:,}")
        print(f"  Indexed vectors: {collection_info.indexed_vectors_count:,}")
        print(f"  Status: {collection_info.status}")
        
    except Exception as e:
        print(f"⚠ Could not get collection info: {e}")
    
    # Search test
    print_header("Search Performance Test")
    
    print(f"Running {TOP_K}-NN search tests...")
    
    # Generate test queries
    num_queries = 100
    queries = [generate_random_vector(VECTOR_DIM) for _ in range(num_queries)]
    
    print(f"\nPerforming {num_queries} search queries (top-{TOP_K})...")
    
    search_start = time.time()
    search_times = []
    
    try:
        from qdrant_client.models import SearchParams
        
        for i, query in enumerate(queries):
            query_start = time.time()
            
            results = client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query,
                limit=TOP_K,
                search_params=SearchParams(
                    hnsw_ef=EF_SEARCH  # Set ef parameter for search
                )
            )
            
            query_time = time.time() - query_start
            search_times.append(query_time)
            
            if (i + 1) % 20 == 0:
                avg_time = sum(search_times) / len(search_times)
                print(f"   Completed {i+1}/{num_queries} queries - "
                      f"Avg: {avg_time*1000:.2f}ms")
        
        total_search_time = time.time() - search_start
        avg_search_time = sum(search_times) / len(search_times)
        min_search_time = min(search_times)
        max_search_time = max(search_times)
        
        # Calculate percentiles
        sorted_times = sorted(search_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"\n✓ Search Performance Results:")
        print(f"  Total queries: {num_queries}")
        print(f"  Total time: {total_search_time:.2f}s")
        print(f"  QPS: {num_queries / total_search_time:.1f}")
        print(f"\n  Latency Statistics:")
        print(f"    Average: {avg_search_time*1000:.2f}ms")
        print(f"    Min: {min_search_time*1000:.2f}ms")
        print(f"    Max: {max_search_time*1000:.2f}ms")
        print(f"    P50: {p50*1000:.2f}ms")
        print(f"    P95: {p95*1000:.2f}ms")
        print(f"    P99: {p99*1000:.2f}ms")
        
        # Show sample results
        print(f"\n  Sample search results (first query):")
        sample_results = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=queries[0],
            limit=5,
            search_params=SearchParams(hnsw_ef=EF_SEARCH)
        )
        
        print("   ┌────────┬──────────────┬────────────────┐")
        print("   │ Rank   │ ID           │ Score          │")
        print("   ├────────┼──────────────┼────────────────┤")
        for i, result in enumerate(sample_results):
            print(f"   │ {i+1:6d} │ {result.id:12d} │ {result.score:14.6f} │")
        print("   └────────┴──────────────┴────────────────┘")
        
    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print_header("Test Summary")
    
    print(f"✅ Qdrant Performance Test Completed Successfully!")
    print(f"\n📊 Summary:")
    print(f"  Dataset: {NUM_VECTORS:,} vectors × {VECTOR_DIM} dimensions")
    print(f"  Index: HNSW (M={M}, ef_construction={EF_CONSTRUCTION}, ef={EF_SEARCH})")
    print(f"  Insert Time: {format_time(insert_time)}")
    print(f"  Insert Rate: {insert_rate:.0f} vectors/sec")
    print(f"  Search QPS: {num_queries / total_search_time:.1f}")
    print(f"  Avg Search Latency: {avg_search_time*1000:.2f}ms")
    print(f"  P95 Search Latency: {p95*1000:.2f}ms")
    
    print("\n" + "=" * 70)
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
