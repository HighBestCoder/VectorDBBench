#!/usr/bin/env python3
"""Test VDSS integration"""

import sys
sys.path.insert(0, '/builds/VectorDBBench')

# Test imports
print("Testing VDSS imports...")

try:
    from vectordb_bench.backend.clients.vdss.config import VDSSConfig, VDSSIndexConfig
    print("✓ Config imports successful")
except Exception as e:
    print(f"✗ Config import failed: {e}")
    sys.exit(1)

try:
    from vectordb_bench.backend.clients.vdss.vdss import VDSS
    print("✓ VDSS client import successful")
except Exception as e:
    print(f"✗ VDSS client import failed: {e}")
    sys.exit(1)

try:
    from vectordb_bench.backend.clients.vdss.cli import VDSSHnsw
    print("✓ CLI import successful")
except Exception as e:
    print(f"✗ CLI import failed: {e}")
    sys.exit(1)

# Test config creation
print("\nTesting config creation...")
try:
    config = VDSSConfig(
        grpc_host="localhost",
        grpc_port=50051,
        db_label="test"
    )
    print(f"✓ VDSSConfig created: {config.to_dict()}")
except Exception as e:
    print(f"✗ Config creation failed: {e}")
    sys.exit(1)

try:
    index_config = VDSSIndexConfig(
        m=16,
        ef_construction=200,
        ef_search=100
    )
    print(f"✓ VDSSIndexConfig created")
    print(f"  - Index params: {index_config.index_param()}")
    print(f"  - Search params: {index_config.search_param()}")
except Exception as e:
    print(f"✗ Index config creation failed: {e}")
    sys.exit(1)

print("\n✓ All VDSS integration tests passed!")
print("\nTo use VDSS with vectordbbench CLI:")
print("  vectordbbench vdsshnsw --grpc-host <host> --grpc-port <port> --case-type <case>")
