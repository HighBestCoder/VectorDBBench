#!/usr/bin/env python3
"""
VDSS gRPC Client Example (Python)

This example demonstrates how to use VDSS gRPC service to perform
vector database operations remotely.

Equivalent to the C++ grpc_client_example.cc
"""

import sys
import json
import grpc
import random
import math

sys.path.insert(0, '/builds/VectorDBBench/vdeclient')

import vdss_service_pb2
import vdss_service_pb2_grpc
import vdss_types_pb2

# VDSS Server Configuration
VDSS_HOST = "172.17.0.2"
VDSS_PORT = 50051

# Configuration
VECTOR_DIM = 128
TOP_K = 5
NUM_VECTORS = 30


def generate_random_vector(dim):
    """Generate a random normalized vector"""
    vec = [random.gauss(0, 1) for _ in range(dim)]
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-6:
        vec = [x / norm for x in vec]
    return vec


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_results_table(results, top_k):
    """Print search results in a formatted table"""
    print(f"\n📊 Search Results (Top-{top_k}):")
    print("   ┌────────┬──────────────┬────────────────────────────────┐")
    print("   │ Rank   │ Offset       │ Distance                       │")
    print("   ├────────┼──────────────┼────────────────────────────────┤")
    
    for i, (offset, score) in enumerate(results):
        print(f"   │ {i+1:6d} │ {offset:12d} │ {score:30.6f} │")
    
    print("   └────────┴──────────────┴────────────────────────────────┘")


def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║        VDSS gRPC Client Example (Python)            ║")
    print("║        Vector Search Service via gRPC               ║")
    print("╚══════════════════════════════════════════════════════╝")
    
    server_address = f"{VDSS_HOST}:{VDSS_PORT}"
    print(f"\n🔗 Connecting to VDSS server at: {server_address}")
    
    # Create gRPC channel
    channel = grpc.insecure_channel(server_address)
    stub = vdss_service_pb2_grpc.VDSSServiceStub(channel)
    
    try:
        # ========== Health Check ==========
        print_header("Health Check")
        
        health_req = vdss_service_pb2.HealthCheckRequest()
        health_resp = stub.HealthCheck(health_req)
        
        if health_resp.status.code != 0:
            print("❌ Health check failed! Is the server running?")
            print("Start server with: vdss-grpc-server --port 50051 --engine-path /tmp/vdss_data")
            return 1
        
        print(f"✓ Server is healthy")
        print(f"  Version: {health_resp.version}")
        print(f"  Uptime: {health_resp.uptime_seconds}s")
        
        # ========== Configuration ==========
        print("\n📋 Configuration:")
        print(f"   - Vector Dimension: {VECTOR_DIM}")
        print(f"   - Top-K Results: {TOP_K}")
        print(f"   - Number of Vectors: {NUM_VECTORS}")
        
        # ========== Create Collection ==========
        print_header("Creating Collection")
        
        collection_name = "demo_collection_grpc"
        print(f"Creating collection: {collection_name}")
        
        # Configuration matching C++ example
        config_json = {
            "dtype": "float32",
            "metric_type": "l2",
            "hnsw": {
                "max_degree": 16,
                "ef_construction": 200
            }
        }
        
        config = vdss_types_pb2.CollectionConfig(
            index_type="hnsw",
            storage_type="zendb",
            dimension=VECTOR_DIM,
            distance_metric="l2",
            config_json=json.dumps(config_json)
        )
        
        create_req = vdss_service_pb2.CreateCollectionRequest(
            collection_name=collection_name,
            config=config
        )
        create_resp = stub.CreateCollection(create_req)
        
        if create_resp.status.code != 0:
            print(f"❌ Failed to create collection: {create_resp.status.message}")
            return 1
        
        print("✓ Collection created successfully")
        
        # ========== Insert Vectors ==========
        print_header("Inserting Vectors")
        
        print(f"Inserting {NUM_VECTORS} vectors...")
        success_count = 0
        
        for i in range(NUM_VECTORS):
            vector_data = generate_random_vector(VECTOR_DIM)
            
            payload = {
                "id": i,
                "category": "even" if i % 2 == 0 else "odd",
                "value": i * 100
            }
            
            vector = vdss_types_pb2.Vector(data=vector_data, dimension=VECTOR_DIM)
            payload_pb = vdss_types_pb2.Payload(json=json.dumps(payload))
            
            upsert_req = vdss_service_pb2.UpsertVectorRequest(
                collection_name=collection_name,
                offset=i,
                vector=vector,
                payload=payload_pb
            )
            upsert_resp = stub.UpsertVector(upsert_req)
            
            if upsert_resp.status.code == 0:
                success_count += 1
                if (i + 1) % 10 == 0:
                    print(f"   ✓ Inserted {i+1}/{NUM_VECTORS} vectors")
        
        print(f"✓ Successfully inserted {success_count}/{NUM_VECTORS} vectors")
        
        # ========== KNN Search Test ==========
        print_header("KNN Search Test")
        
        print("Generating random query vector...")
        query_data = generate_random_vector(VECTOR_DIM)
        query_vector = vdss_types_pb2.Vector(data=query_data, dimension=VECTOR_DIM)
        
        search_req = vdss_service_pb2.SearchRequest(
            collection_name=collection_name,
            query=query_vector,
            top_k=TOP_K
        )
        search_resp = stub.Search(search_req)
        
        if search_resp.status.code != 0:
            print(f"❌ Search failed: {search_resp.status.message}")
        else:
            results = [(r.offset, r.score) for r in search_resp.results]
            print_results_table(results, TOP_K)
        
        # ========== Filtered Search Test ==========
        print_header("Filtered Search Test")
        
        filter_json = {
            "must": [
                {"key": "category", "match": {"value": "even"}}
            ]
        }
        
        print("Searching with filter: category = 'even'...")
        
        filtered_search_req = vdss_service_pb2.SearchFilteredRequest(
            collection_name=collection_name,
            query=query_vector,
            top_k=TOP_K,
            filter_json=json.dumps(filter_json)
        )
        filtered_search_resp = stub.SearchFiltered(filtered_search_req)
        
        if filtered_search_resp.status.code != 0:
            print(f"❌ Filtered search failed: {filtered_search_resp.status.message}")
        else:
            filtered_results = [(r.offset, r.score) for r in filtered_search_resp.results]
            print(f"\n📊 Filtered Search Results (Top-{TOP_K}):")
            print_results_table(filtered_results, TOP_K)
        
        # ========== Get Vector Test ==========
        print_header("Get Vector Test")
        
        if search_resp.status.code == 0 and len(search_resp.results) > 0:
            test_offset = search_resp.results[0].offset
            print(f"Getting vector with offset {test_offset}...")
            
            get_req = vdss_service_pb2.GetVectorRequest(
                collection_name=collection_name,
                offset=test_offset
            )
            get_resp = stub.GetVector(get_req)
            
            if get_resp.status.code == 0:
                print("✓ Vector retrieved successfully!")
                print(f"   Dimension: {len(get_resp.vector.data)}")
                print(f"   Payload: {get_resp.payload.json}")
                vec_data = list(get_resp.vector.data)
                print(f"   First 5 values: [{', '.join(f'{v:.6f}' for v in vec_data[:5])}, ...]")
        
        # ========== Delete Vector Test ==========
        print_header("Delete Vector Test")
        
        delete_offset = 10
        print(f"Deleting vector with offset {delete_offset}...")
        
        delete_req = vdss_service_pb2.DeleteVectorRequest(
            collection_name=collection_name,
            offset=delete_offset
        )
        delete_resp = stub.DeleteVector(delete_req)
        
        if delete_resp.status.code == 0:
            print("✓ Vector deleted successfully!")
            
            # Verify deletion
            verify_req = vdss_service_pb2.GetVectorRequest(
                collection_name=collection_name,
                offset=delete_offset
            )
            verify_resp = stub.GetVector(verify_req)
            
            if verify_resp.status.code != 0:
                print("✓ Verification: Vector no longer exists")
        
        # ========== Statistics ==========
        print_header("Collection Statistics")
        
        count_req = vdss_service_pb2.GetVectorCountRequest(
            collection_name=collection_name
        )
        count_resp = stub.GetVectorCount(count_req)
        
        if count_resp.status.code == 0:
            print(f"Total vectors: {count_resp.count}")
            print(f"Collection name: {collection_name}")
        
        # ========== Cleanup ==========
        print_header("Cleanup & Shutdown")
        
        print("Closing collection...")
        close_req = vdss_service_pb2.CloseCollectionRequest(
            collection_name=collection_name
        )
        close_resp = stub.CloseCollection(close_req)
        
        if close_resp.status.code == 0:
            print("✓ Collection closed successfully")
        
        print("\n╔══════════════════════════════════════════════════════╗")
        print("║          Program Completed Successfully              ║")
        print("╚══════════════════════════════════════════════════════╝")
        
        return 0
        
    except grpc.RpcError as e:
        print(f"\n❌ gRPC Error: {e.code()}")
        print(f"   Details: {e.details()}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        channel.close()


if __name__ == "__main__":
    sys.exit(main())
